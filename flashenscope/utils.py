# flashenscope/utils.py

def describeDroppedFrames(meta):
    """Print a summary of frame drops from metadata."""
    dropped = meta.get("Dropped_Frames", 0)
    saved = meta.get("Frames_Saved", 0)
    if dropped == 0:
        print("✅ No frames dropped!")
    else:
        frac = 100 * dropped / (saved + dropped)
        print(f"⚠️ Dropped {dropped} frames ({frac:.2f}% loss).")