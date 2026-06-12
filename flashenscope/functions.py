# flashenscope/functions.py
import numpy as np
import matplotlib.pyplot as plt
import imageio.v3 as iio
import time
import os
import cv2
from pymmcore_plus import CMMCorePlus
import threading
import tkinter as tk
from flashenscope.core import get_core
from math import ceil
import sys
import json

def initialize():
    """Initialize Micro-Manager Core."""
    print('Establishing connections...')
    mm_path = r"C:\Program Files\Micro-Manager-2.0"
    os.environ["MMCORE_PATH"] = mm_path
    mmc = get_core()    
    mmc.waitForSystem()
    print('All systems go ✅')
    mmc.setZPosition(0)
    return mmc
    
# ---------- Live preview ----------

def live(config=None):
    mmc = get_core()

    if config:
        print(f"Switching to channel config: {config}", flush=True)
        mmc.setConfig('Channel', config)
        mmc.waitForSystem()

    zoom_state = {"on": False, "running": True}

    # ---- Video loop (background thread) ----
    def video_loop():
        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
        mmc.startContinuousSequenceAcquisition(1)
        print("🎥 Live preview started. Close Tk window or press any key in Video window to stop.")

        try:
            from screeninfo import get_monitors
            screen_w, screen_h = get_monitors()[0].width, get_monitors()[0].height
        except Exception:
            screen_w, screen_h = 1920, 1080

        scale_max = 0.9

        while zoom_state["running"]:
            if mmc.getRemainingImageCount() > 0:
                img = mmc.getLastImage()

                if img.dtype != np.uint8:
                    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

                frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                h, w = frame.shape[:2]
                frame[img >= 255] = [0, 0, 255]

                # ---- Zoom ----
                zoom_on = zoom_state["on"]
                zoom_factor = 4
                zh, zw = h // zoom_factor, w // zoom_factor
                y0, x0 = (h - zh) // 2, (w - zw) // 2

                if zoom_on:
                    frame = cv2.resize(frame[y0:y0+zh, x0:x0+zw], (w, h), interpolation=cv2.INTER_NEAREST)
                else:
                    cv2.rectangle(frame, (x0, y0), (x0+zw, y0+zh), (0, 255, 0), 1)

                scale = min((screen_w * scale_max) / w, (screen_h * scale_max) / h)
                disp_w, disp_h = int(w * scale), int(h * scale)
                frame_disp = cv2.resize(frame, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
                cv2.imshow("Video", frame_disp)

            if cv2.waitKey(1) >= 0:
                zoom_state["running"] = False

        mmc.stopSequenceAcquisition()
        mmc.waitForSystem()
        cv2.destroyAllWindows()
        print("🛑 Live preview stopped.")

    # ---- Tkinter control window ----
    def on_close():
        zoom_state["running"] = False
        root.destroy()

    root = tk.Tk()
    root.title("MM Controls")
    root.geometry("160x100+50+50")
    root.configure(bg="#2b2b2b")  # dark gray background
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Custom toggle switch
    toggle_canvas = tk.Canvas(root, width=60, height=30, highlightthickness=0, bg="#2b2b2b")
    toggle_canvas.pack(pady=20)

    # Draw background and knob
    bg_rect = toggle_canvas.create_oval(2, 2, 28, 28, fill="#555555", outline="")  # dark gray off
    knob = toggle_canvas.create_oval(2, 2, 28, 28, fill="#f0f0f0", outline="")      # light knob

    def update_toggle():
        if zoom_state["on"]:
            toggle_canvas.itemconfig(bg_rect, fill="#4CAF50")  # green on
            toggle_canvas.coords(knob, 30, 2, 56, 28)
        else:
            toggle_canvas.itemconfig(bg_rect, fill="#555555")   # dark gray off
            toggle_canvas.coords(knob, 2, 2, 28, 28)

    def toggle_zoom(event=None):
        zoom_state["on"] = not zoom_state["on"]
        update_toggle()

    toggle_canvas.bind("<Button-1>", toggle_zoom)

    label = tk.Label(root, text="Zoom", font=("Segoe UI", 10), fg="white", bg="#2b2b2b")
    label.pack()

    update_toggle()

    # Start OpenCV in background
    threading.Thread(target=video_loop, daemon=True).start()

    root.mainloop()

def takePicture(config=None, ROI=None, save_path=None, show_picture =False):
    mmc = get_core()

    if config:
        mmc.setConfig('Channel', config)
        mmc.waitForSystem()
        current_config = config

    # Check current config - does not work if config is defined as input in function (we don't use this)
    # current_config = mmc.getCurrentConfig('Channel')
    # print(f"Current config: {current_config}", flush=True)

    # lamp_on = False
    # if "tr" in current_config.lower():
    #     try:
    #         mmc.setConfig('lamp', 'on')
    #         mmc.waitForSystem()
    #         lamp_on = True
    #         print("💡 Lamp turned ON (waiting 5s)...", flush=True)
    #         time.sleep(5)
    #    except Exception as e:
    #        print(f"Warning: could not turn lamp on ({e})", flush=True)

    # Snap image
    # print("📸 Snapping image...", flush=True)
    mmc.snapImage()
    img = mmc.getImage()

    # Convert to numpy
    dtype = np.uint16 if mmc.getBytesPerPixel() == 2 else np.uint8
    img = np.array(img, dtype=dtype)

    # Turn lamp off
    #if lamp_on:
    #    try:
    #        mmc.setConfig('lamp', 'off')
    #        mmc.waitForSystem()
    #        print("💡 Lamp turned OFF.", flush=True)
    #    except Exception as e:
    #        print(f"Warning: could not turn lamp off ({e})", flush=True)

    # Display
    if show_picture:
        plt.figure()
        plt.imshow(img, cmap='gray')
        plt.title('Snapped Image')
        plt.axis('off')
        plt.show(block=False)

    if save_path:
        iio.imwrite(save_path, img)
        print(f"💾 Saved to {save_path}", flush=True)

    return img


def sequenceAcquisition(file_name, runtime, config, bit8=False, ROI=None):

    import os
    import sys
    import json
    import time
    import numpy as np
    from math import ceil

    mmc = get_core()

    # -----------------------------
    # Configure microscope
    # -----------------------------
    mmc.setConfig('Channel', config)
    mmc.waitForSystem()

    camera = mmc.getCameraDevice()

    interval_ms = float(mmc.getProperty(camera, 'Exposure'))
    interval_s = interval_ms / 1000.0

    print(
        f"Config={config} | "
        f"Exposure={interval_ms:.3f} ms"
    )

    # -----------------------------
    # Bit depth
    # -----------------------------
    bytes_per_pixel = mmc.getBytesPerPixel()

    if bytes_per_pixel == 1:
        pixel_type = np.uint8
    else:
        pixel_type = np.uint16

    # -----------------------------
    # ROI
    # -----------------------------
    if ROI is not None:
        x, y, w_roi, h_roi = ROI

        mmc.setROI(
            int(x),
            int(y),
            int(w_roi),
            int(h_roi)
        )
        mmc.waitForSystem()

    w = mmc.getImageWidth()
    h = mmc.getImageHeight()

    print(f"ROI = {w} x {h}")

    # -----------------------------
    # Expected frame count
    # -----------------------------
    nImages = ceil(runtime / interval_s)

    # -----------------------------
    # Output files
    # -----------------------------
    bin_path = file_name + ".bin"
    meta_path = file_name + "_meta.json"

    if os.path.exists(bin_path):
        print(f"⚠️ File already exists: {bin_path}")
        return

    f = open(bin_path, "wb")

    print(
        f"Recording {nImages} frames "
        f"({runtime:.1f}s at {1/interval_s:.2f} fps)"
    )
    print(f"Saving to: {bin_path}")

    sys.stdout.flush()

    # -----------------------------
    # Circular buffer
    # -----------------------------
    mmc.setCircularBufferMemoryFootprint(32000)
    mmc.initializeCircularBuffer()

    mmc.prepareSequenceAcquisition(camera)
    mmc.waitForSystem()

    mmc.startContinuousSequenceAcquisition(interval_ms)

    # -----------------------------
    # Acquisition
    # -----------------------------
    frame_counter = 0

    t_detect = []
    dt_process = []

    print("Acquiring...", flush=True)

    t0 = time.time()

    try:

        while time.time() - t0 < runtime:

            while mmc.getRemainingImageCount() > 0:

                t1 = time.time()

                img = mmc.popNextImage()

                img = np.asarray(img, dtype=pixel_type)

                if bit8 and bytes_per_pixel > 1:
                    img = (img / 256).astype(np.uint8)

                img.tofile(f)

                frame_counter += 1

                t_detect.append(time.time() - t0)
                dt_process.append(time.time() - t1)

            time.sleep(0.0005)

    except KeyboardInterrupt:

        print("Acquisition interrupted by user.")

    finally:

        # Drain any remaining frames
        while mmc.getRemainingImageCount() > 0:

            img = mmc.popNextImage()

            img = np.asarray(img, dtype=pixel_type)

            if bit8 and bytes_per_pixel > 1:
                img = (img / 256).astype(np.uint8)

            img.tofile(f)

            frame_counter += 1

        mmc.stopSequenceAcquisition()
        mmc.waitForSystem()

        f.close()

        mmc.clearCircularBuffer()
        mmc.clearROI()

    # -----------------------------
    # Statistics
    # -----------------------------
    dropped_frames = max(0, nImages - frame_counter)

    print(f"Saved {frame_counter} frames.")
    print(f"Dropped frames: {dropped_frames}")

    # -----------------------------
    # Configuration metadata
    # -----------------------------
    cfgmeta = mmc.getConfigData('Channel', config)

    cfg_dict = {}

    for dev, prop, val in cfgmeta:
        cfg_dict.setdefault(dev, {})
        cfg_dict[dev][prop] = val

    # -----------------------------
    # Save metadata
    # -----------------------------
    meta = {
        'Config': config,
        'Runtime_sec': runtime,
        'Exposure_ms': interval_ms,
        'Frames_Requested': int(nImages),
        'Frames_Saved': int(frame_counter),
        'Dropped_Frames': int(dropped_frames),
        'Resolution': {
            'Width': int(w),
            'Height': int(h),
        },
        'BitDepth': 8 if bit8 else bytes_per_pixel * 8,
        'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'Configuration': cfg_dict,
        't_detect': t_detect,
        'dt_process': dt_process,
        'scope_metadata': mmc.getTags(),
    }

    with open(meta_path, 'w') as mf:
        json.dump(meta, mf, indent=2)

    print(f"Metadata saved to: {meta_path}")
    print("✅ Acquisition complete.")