import time
from movement_metrics import MovementMetrics


def test_grasp_quality_and_reaction_time():
    m = MovementMetrics()
    assert m.grasp_quality() == 0.0
    assert m.reaction_time() is None
    start = time.time()
    m.start_session(start)
    # no success yet
    assert m.reaction_time() is None
    # record a failed grasp
    m.add_grasp_event(False, ts=start + 0.5)
    assert m.grasp_quality() == 0.0
    # record success
    m.add_grasp_event(True, ts=start + 1.5)
    m.record_first_success(start + 1.5)
    assert abs(m.reaction_time() - 1.5) < 0.01
    assert m.grasp_quality() == 50.0


def test_smoothness_basic():
    m = MovementMetrics(window_size=10)
    # Add linear positions -> low jerk -> high smoothness
    for i in range(10):
        m.add_position(i, 0)
    s = m.smoothness()
    assert s >= 0.0 and s <= 100.0
