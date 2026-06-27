"""
Planetary Habitability and Classification Estimator
Estimates planet size, orbital characteristics, equilibrium temperature,
stellar irradiation, and habitability zone boundaries.
"""
import numpy as np
from typing import Dict


def calculate_semi_major_axis(period_days: float, M_star: float = 1.0) -> float:
    """
    Calculate semi-major axis (a) in AU using Kepler's Third Law.
    a^3 = P^2 * M_star (where P is in years, M in solar masses, a in AU)
    """
    period_years = period_days / 365.25
    a = (period_years**2 * M_star) ** (1/3)
    return float(a)


def calculate_equilibrium_temperature(period_days: float, R_star: float = 1.0, 
                                      T_eff: float = 5778, M_star: float = 1.0,
                                      bond_albedo: float = 0.3) -> float:
    """
    Estimate planetary equilibrium temperature in Kelvin.
    T_eq = T_eff * sqrt(R_star / (2 * a)) * (1 - A_B)^(1/4)
    where a is in stellar units (converted to AU, then to solar radii or R_star units)
    """
    a_au = calculate_semi_major_axis(period_days, M_star)
    # Convert AU to Solar Radii (1 AU ≈ 215 R_sun)
    a_stellar_units = a_au * 215.03
    
    T_eq = T_eff * np.sqrt(R_star / (2 * a_stellar_units)) * ((1 - bond_albedo) ** 0.25)
    return float(T_eq)


def classify_planet_radius(rp_earth: float) -> str:
    """Classify planet type based on radius in Earth radii."""
    if rp_earth < 0.8:
        return "Sub-Earth"
    elif rp_earth < 1.25:
        return "Earth-like"
    elif rp_earth < 2.0:
        return "Super-Earth"
    elif rp_earth < 6.0:
        return "Warm Neptune"
    else:
        return "Hot Jupiter"


def classify_habitability(period: float, depth: float, R_star: float = 1.0,
                         M_star: float = 1.0, T_eff: float = 5778) -> Dict:
    """
    Perform full classification and habitability estimation.
    """
    # Rp/Rs is approx sqrt(depth)
    rp_rs = np.sqrt(depth)
    # Earth radius relative to Sun is 0.00915
    rp_earth = (rp_rs * R_star) / 0.00915
    
    a_au = calculate_semi_major_axis(period, M_star)
    T_eq = calculate_equilibrium_temperature(period, R_star, T_eff, M_star)
    
    # Stellar flux relative to Earth (irradiation)
    # F = L_star / a^2 where L_star = (R_star)^2 * (T_eff / 5778)^4
    L_star = (R_star ** 2) * ((T_eff / 5778.0) ** 4)
    irradiation = L_star / (a_au ** 2) if a_au > 0 else 0.0
    
    # Habitable Zone classification (simple optimistic zone: 175 K < T_eq < 270 K)
    is_habitable_zone = 175.0 <= T_eq <= 310.0
    radius_class = classify_planet_radius(rp_earth)
    
    # Calculate habitability score (0.0 to 1.0)
    # T_eq close to 255K (Earth's eq temp) and Earth-like size maximizes score
    temp_score = np.exp(-0.5 * ((T_eq - 255.0) / 50.0) ** 2)
    radius_score = np.exp(-0.5 * ((rp_earth - 1.0) / 0.5) ** 2)
    habitability_score = float(temp_score * radius_score if is_habitable_zone else 0.0)
    
    planet_type = radius_class
    if is_habitable_zone:
        if radius_class in ("Earth-like", "Super-Earth"):
            planet_type = f"Potentially Habitable {radius_class}"
        else:
            planet_type = f"Habitable Zone {radius_class}"
            
    return {
        "semi_major_axis_au": float(a_au),
        "equilibrium_temp_k": float(T_eq),
        "stellar_irradiation": float(irradiation),
        "planet_radius_earth": float(rp_earth),
        "radius_class": radius_class,
        "is_habitable_zone": bool(is_habitable_zone),
        "planet_type": planet_type,
        "habitability_score": float(habitability_score),
    }
