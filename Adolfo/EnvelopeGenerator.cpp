#include "EnvelopeGenerator.h"

namespace
{
constexpr float kFallbackUpdateRate = 1000.0f;
constexpr float kMinimumStageTime   = 0.000001f;

float Clamp01(float value)
{
    if(value < 0.0f)
        return 0.0f;
    if(value > 1.0f)
        return 1.0f;
    return value;
}
} // namespace

void EnvelopeGenerator::Init(float updateRate)
{
    update_rate_ = updateRate > 0.0f ? updateRate : kFallbackUpdateRate;
    stage_       = Stage::Idle;
    curve_       = CurveType::Logarithmic;
    value_       = 0.0f;
    phase_       = 0.0f;
    rise_time_   = 0.1f;
    fall_time_   = 0.1f;
    cycling_     = false;
    UpdatePhaseIncrements();
}

void EnvelopeGenerator::Trigger()
{
    // In LFO il trigger riporta il ciclo all'inizio, utile per sincronizzarlo.
    // In AD è accettato solo da Idle: un ciclo già in corso non viene interrotto.
    if(cycling_)
    {
        stage_ = Stage::Rise;
        phase_ = 0.0f;
        value_ = 0.0f;
    }
    else if(stage_ == Stage::Idle)
    {
        stage_ = Stage::Rise;
        phase_ = 0.0f;
        value_ = 0.0f;
    }
}

void EnvelopeGenerator::Stop()
{
    cycling_ = false;
    stage_ = Stage::Idle;
    phase_ = 0.0f;
    value_ = 0.0f;
}

void EnvelopeGenerator::SetCycling(bool enabled)
{
    if(enabled == cycling_)
        return;

    cycling_ = enabled;
    phase_   = 0.0f;
    value_   = 0.0f;

    // Entrando in LFO si parte subito da zero. Tornando in AD si forza Idle.
    stage_ = cycling_ ? Stage::Rise : Stage::Idle;
}

void EnvelopeGenerator::SetRiseTime(float seconds)
{
    rise_time_ = seconds > kMinimumStageTime ? seconds : kMinimumStageTime;
    rise_phase_increment_ = 1.0f / (rise_time_ * update_rate_);
}

void EnvelopeGenerator::SetFallTime(float seconds)
{
    fall_time_ = seconds > kMinimumStageTime ? seconds : kMinimumStageTime;
    fall_phase_increment_ = 1.0f / (fall_time_ * update_rate_);
}

void EnvelopeGenerator::SetCurve(CurveType curve)
{
    curve_ = curve;
}

float EnvelopeGenerator::Process()
{
    switch(stage_)
    {
        case Stage::Idle:
            value_ = 0.0f;
            break;

        case Stage::Rise:
        {
            // L'incremento è precomputato quando cambia il tempo: nel callback
            // restano soltanto curve, somme e confronti. Rise parte da zero.
            value_ = ApplyCurve(phase_);
            phase_ += rise_phase_increment_;

            if(phase_ >= 1.0f)
            {
                // Fall con fase zero produrrà esattamente il picco 1.0.
                phase_ = 0.0f;
                stage_ = Stage::Fall;
            }
        }
        break;

        case Stage::Fall:
        {
            // Fall usa l'inverso della stessa curva crescente selezionata.
            value_ = 1.0f - ApplyCurve(phase_);
            phase_ += fall_phase_increment_;

            if(phase_ >= 1.0f)
            {
                phase_ = 0.0f;
                value_ = 0.0f;
                stage_ = cycling_ ? Stage::Rise : Stage::Idle;
            }
        }
        break;
    }

    return Clamp01(value_);
}

float EnvelopeGenerator::GetValue() const
{
    return value_;
}

Stage EnvelopeGenerator::GetStage() const
{
    return stage_;
}

bool EnvelopeGenerator::IsCycling() const
{
    return cycling_;
}

void EnvelopeGenerator::UpdatePhaseIncrements()
{
    // Come nel motore a segmenti di Mutable Instruments Peaks, l'avanzamento
    // usa un passo di fase esplicito. Qui viene calcolato quando cambia il
    // parametro, così il callback deve soltanto accumularlo.
    rise_phase_increment_ = 1.0f / (rise_time_ * update_rate_);
    fall_phase_increment_ = 1.0f / (fall_time_ * update_rate_);
}

float EnvelopeGenerator::ApplyCurve(float phase) const
{
    phase = Clamp01(phase);

    // Famiglia concava/lineare/convessa analoga alle tabelle di Peaks, qui
    // calcolata con cubiche per rispettare le curve richieste senza lookup table
    // né powf nel callback del timer.
    switch(curve_)
    {
        case CurveType::Linear: return phase;

        case CurveType::Exponential: return phase * phase * phase;

        case CurveType::Logarithmic:
        {
            const float inverse = 1.0f - phase;
            return 1.0f - (inverse * inverse * inverse);
        }
    }

    return phase;
}
