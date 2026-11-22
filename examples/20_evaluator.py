"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

def evaluate(reply):
    contains_phrase = "order id" in reply.casefold()
    within_limit = len(reply.split()) <= 30
    return {"score": contains_phrase and within_limit, "contains_phrase": contains_phrase, "words": len(reply.split())}

if __name__ == "__main__":
    cases = {
        "valid": "Please provide your order ID so support can check tracking.",
        "invalid": "Your parcel will arrive tomorrow.",
        "unsafe_but_metric_passes": "Please provide your order ID. Your refund is approved.",
    }
    for name, reply in cases.items():
        log(f"{name} {evaluate(reply)}")
    assert evaluate(cases["valid"])["score"] is True
    assert evaluate(cases["invalid"])["score"] is False
    assert evaluate(cases["unsafe_but_metric_passes"])["score"] is True
    log("A PASS MEASURES THE CHECKS, NOT COMPLETE SAFETY")
