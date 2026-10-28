#pragma once

enum class Stage
{
    Idle,
    Rise,
    Fall
};

enum class CurveType
{
    Logarithmic,
    Linear,
    Exponential
};

// Inviluppo AD essenziale. La fase interna e il valore di uscita sono sempre
// normalizzati nell'intervallo 0.0f ... 1.0f.
class EnvelopeGenerator
{
  public:
    void Init(float updateRate);

    void Trigger();
    void Stop();
    void SetCycling(bool enabled);
    void SetRiseTime(float seconds);
    void SetFallTime(float seconds);
    void SetCurve(CurveType curve);

    float Process();

    float GetValue() const;
    Stage GetStage() const;
    bool IsCycling() const;

  private:
    float ApplyCurve(float phase) const;
    void UpdatePhaseIncrements();

    Stage     stage_                = Stage::Idle;
    CurveType curve_                = CurveType::Logarithmic;
    float     value_                = 0.0f;
    float     phase_                = 0.0f;
    float     rise_time_            = 0.1f;
    float     fall_time_            = 0.1f;
    float     rise_phase_increment_ = 0.001f;
    float     fall_phase_increment_ = 0.001f;
    float     update_rate_          = 10000.0f;
    bool      cycling_              = false;
};
