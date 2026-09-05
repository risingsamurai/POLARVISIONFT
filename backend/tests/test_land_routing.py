"""Comprehensive test suite for land mask avoidance and dynamic hazard separation in POLARIS router."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.land_mask import is_land, is_segment_land
from ml.astar_router import three_routes, _haversine_nm, _ice_at, _berg_penalty


def test_south_georgia_land_avoidance():
    """1 & 4. Test start/dest across South Georgia Island to confirm all 3 routes avoid land."""
    start = [-54.0, -38.0]
    dest = [-54.5, -35.0]

    # Verify straight line crosses South Georgia land
    assert is_segment_land((start[0], start[1]), (dest[0], dest[1])), "Straight line MUST cross South Georgia land!"

    routes = three_routes(start, dest, bergs=[])
    assert len(routes) == 3

    for r in routes:
        pts = r["points"]
        land_points = [p for p in pts if is_land(p["lat"], p["lon"])]
        assert len(land_points) == 0, f"Route '{r['name']}' crossed land! Land points: {land_points}"
        
        # Verify no segment crosses land
        for a, b in zip(pts, pts[1:]):
            assert not is_segment_land((a["lat"], a["lon"]), (b["lat"], b["lon"]), num_samples=8), \
                f"Route '{r['name']}' segment between {a} and {b} crossed land!"

    print("\n[PASSED] South Georgia Test: All 3 routes (Safest, Balanced, Fastest) completely avoided land!")


def test_iceberg_hazard_separation():
    """2 & 3. Test closest-approach distance to an iceberg sitting in the path."""
    start = [-60.0, -48.0]
    dest = [-60.0, -44.0]
    hazard_berg = {"id": "A-88", "lat": -60.0, "lon": -46.0, "radius": 15.0}
    bergs = [hazard_berg]

    routes = three_routes(start, dest, bergs)
    distances = {}
    risk_scores = {}

    def get_min_clearance(pts, b):
        min_d = 9999.0
        b_pos = (b["lat"], b["lon"])
        for a, b_pt in zip(pts, pts[1:]):
            for i in range(15):
                t = i / 15.0
                lat = a["lat"] + (b_pt["lat"] - a["lat"]) * t
                lon = a["lon"] + (b_pt["lon"] - a["lon"]) * t
                d = _haversine_nm((lat, lon), b_pos)
                if d < min_d:
                    min_d = d
        return min_d

    for r in routes:
        rid = r["id"]
        pts = r["points"]
        distances[rid] = round(get_min_clearance(pts, hazard_berg), 2)
        risk_scores[rid] = r["riskScore"]

    print("\n--- ICEBERG HAZARD SEPARATION TEST RESULTS ---")
    print(f"Hazard Iceberg Position: ({hazard_berg['lat']}, {hazard_berg['lon']})")
    print(f"Safest Route:   Closest Distance = {distances['safest']} NM, Dynamic Risk Score = {risk_scores['safest']}")
    print(f"Balanced Route: Closest Distance = {distances['balanced']} NM, Dynamic Risk Score = {risk_scores['balanced']}")
    print(f"Fastest Route:  Closest Distance = {distances['fastest']} NM, Dynamic Risk Score = {risk_scores['fastest']}")

    # Quantitative assertions: Safest > Balanced > Fastest distance clearance
    assert distances["safest"] > distances["balanced"], \
        f"Safest clearance ({distances['safest']} NM) should be > Balanced ({distances['balanced']} NM)"
    assert distances["balanced"] >= distances["fastest"], \
        f"Balanced clearance ({distances['balanced']} NM) should be >= Fastest ({distances['fastest']} NM)"
    
    # Risk score assertions: Safest < Balanced < Fastest risk score
    assert risk_scores["safest"] < risk_scores["balanced"] < risk_scores["fastest"], \
        f"Risk scores must follow Safest < Balanced < Fastest! Got: {risk_scores}"


def test_sea_ice_field_avoidance():
    """4. Test high sea ice field area avoidance."""
    start = [-68.0, -65.0]
    dest = [-68.0, -58.0]
    
    routes = three_routes(start, dest, bergs=[])
    
    safest = next(r for r in routes if r["id"] == "safest")
    fastest = next(r for r in routes if r["id"] == "fastest")
    
    print("\n--- SEA ICE FIELD TEST RESULTS ---")
    print(f"Safest Route Distance:  {safest['distanceNm']} NM, Risk Score: {safest['riskScore']}")
    print(f"Fastest Route Distance: {fastest['distanceNm']} NM, Risk Score: {fastest['riskScore']}")
    
    assert safest["riskScore"] < fastest["riskScore"], "Safest route must have lower risk score than Fastest!"


if __name__ == "__main__":
    test_south_georgia_land_avoidance()
    test_iceberg_hazard_separation()
    test_sea_ice_field_avoidance()
