from pymmcore_plus import CMMCorePlus
import numpy as np
import cv2
import time
import matplotlib.pyplot as plt
import imageio.v3 as iio
import sys, os, json
from math import ceil, floor

def initialize():
    print('Establishing connections...')
    mm_path = r"C:\Program Files\Micro-Manager-2.0"
    os.environ["MMCORE_PATH"] = mm_path
    cfg_path = r"C:\Users\Flash\Documents\GitHub\flashenscope\flashenscope.cfg"
    camera_name = "HamamatsuHam_DCAM" 

    mmc = CMMCorePlus.instance()
    mmc.loadSystemConfiguration(cfg_path)    
    # mmc.setConfig('System', 'Startup')
    mmc.waitForSystem()
    
    print('Initialization successful!')

    return mmc


def live(mmc, config):
    # --- Setup ---
    mmc.setConfig('Channel', config)
    mmc.waitForSystem()
    camera = mmc.getCameraDevice()

    cv2.namedWindow('Video', cv2.WINDOW_NORMAL)
    cv2.namedWindow('MM controls', cv2.WINDOW_NORMAL)

    # --- Zoom toggle control ---
    zoom_state = {'on': 0}
    def on_zoom_toggle(v):
        zoom_state['on'] = v
    cv2.createTrackbar('Zoom (0=off,1=on)', 'MM controls', 0, 1, on_zoom_toggle)

    mmc.startContinuousSequenceAcquisition(1)
    print("Live preview started. Press any key in the Video window to stop.")

    # Detect monitor size (approx) to fit window
    screen_w, screen_h = 1920, 1080  # fallback defaults
    try:
        from screeninfo import get_monitors
        mon = get_monitors()[0]
        screen_w, screen_h = mon.width, mon.height
    except Exception:
        pass

    scale_max = 0.9  # occupy at most 90% of screen

    try:
        while True:
            if mmc.getRemainingImageCount() > 0:
                img = mmc.getLastImage()

                # Normalize to 8-bit
                if img.dtype != np.uint8:
                    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

                frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                h, w = frame.shape[:2]

                # Highlight saturated pixels
                frame[img >= 255] = [0, 0, 255]

                # Zoom logic
                zoom_on = bool(zoom_state['on'])
                zoom_factor = 4
                zh, zw = h // zoom_factor, w // zoom_factor
                y0, x0 = (h - zh) // 2, (w - zw) // 2

                if zoom_on:
                    cropped = frame[y0:y0+zh, x0:x0+zw]
                    frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_NEAREST)
                else:
                    # Draw zoom region grid
                    cv2.rectangle(frame, (x0, y0), (x0+zw, y0+zh), (0, 255, 0), 1)
                    for i in range(1, zoom_factor):
                        cv2.line(frame,
                                 (x0 + i*zw//zoom_factor, y0),
                                 (x0 + i*zw//zoom_factor, y0+zh),
                                 (0, 255, 0), 1)
                        cv2.line(frame,
                                 (x0, y0 + i*zh//zoom_factor),
                                 (x0+zw, y0 + i*zh//zoom_factor),
                                 (0, 255, 0), 1)

                # Compute display size maintaining aspect ratio to fit screen
                scale = min((screen_w * scale_max) / w, (screen_h * scale_max) / h)
                disp_w, disp_h = int(w * scale), int(h * scale)
                frame_disp = cv2.resize(frame, (disp_w, disp_h), interpolation=cv2.INTER_AREA)

                cv2.imshow('Video', frame_disp)
                cv2.resizeWindow('Video', disp_w, disp_h)

            # Press any key to quit
            if cv2.waitKey(1) >= 0:
                break

    finally:
        mmc.stopSequenceAcquisition()
        mmc.waitForSystem()
        cv2.destroyAllWindows()
        print("Live preview stopped.")


def takePicture(mmc, config=None, ROI=None, save_path=None, lamp_warmup=3):
    """
    Snaps an image using the current or specified configuration.

    Parameters
    ----------
    mmc : CMMCorePlus
        The Micro-Manager core instance.
    config : str, optional
        Channel configuration name (e.g. 'tr_10x_20fps'). If None, uses current channel.
    ROI : tuple, optional
        ROI as (x, y, width, height).
    save_path : str, optional
        File path to save the image (e.g. 'image.tif').
    lamp_warmup : float, optional
        Seconds to wait for transmitted lamp to turn on (default 3s).

    Returns
    -------
    img : np.ndarray
        The captured image.
    """

    # --- Apply channel configuration if provided ---
    if config:
        print(f"Switching to channel config: {config}", flush=True)
        mmc.setConfig('Channel', config)
        mmc.waitForSystem()        
        time.sleep(0.1)  # tiny delay to let devices settle

    lamp_on = False

    # --- Turn on transmitted lamp if channel contains "tr" ---
    if config and "tr" in config.lower():
        print("Turning on transmitted lamp...", flush=True)
        mmc.setConfig('lamp', 'on')
        lamp_on = True
        mmc.waitForSystem()
        print("Waiting 5 seconds for lamp warm-up...", flush=True)
        time.sleep(5)

    # --- Apply ROI if provided ---
    if ROI:
        print(f"Applying ROI: {ROI}", flush=True)
        mmc.setROI(*ROI)

    # --- Snap image ---
    print("Snapping image...", flush=True)
    mmc.snapImage()
    img = mmc.getImage()

    # --- Convert to numpy array ---
    if mmc.getBytesPerPixel() == 2:
        img = np.array(img, dtype=np.uint16)
    else:
        img = np.array(img, dtype=np.uint8)

    # --- Clear ROI ---
    if ROI:
        mmc.clearROI()

    # --- Turn off lamp if it was turned on ---
    if lamp_on:
        try:
            print("Turning lamp off...", flush=True)
            mmc.setConfig('lamp', 'off')
            mmc.waitForSystem()
            print("Lamp turned off", flush=True)
        except Exception as e:
            print(f"Warning: could not turn lamp off ({e})", flush=True)

    # --- Display the image ---
    plt.figure()
    plt.imshow(img, cmap='gray')
    plt.title(f"Snapped Image ({current_config})")
    plt.axis('off')
    plt.show(block=True)

    # --- Optionally save ---
    if save_path:
        iio.imwrite(save_path, img)
        print(f"Saved image to {save_path}", flush=True)

    return img



def sequenceAcquisition(mmc, file_name, runtime, config, bit8=False, ROI=None):
    """
    Acquire a continuous sequence and save as a raw binary stream.

    Parameters
    ----------
    mmc : CMMCorePlus
        Micro-Manager core instance.
    file_name : str
        Output file name (without extension).
    runtime : float
        Total acquisition time (seconds).
    config : str
        Channel configuration (e.g. 'tr_10x_20fps').
    bit8 : bool, optional
        Whether to convert to 8-bit before writing (default False).
    ROI : tuple, optional
        ROI as (x, y, width, height).

    Saves
    -----
    - file_name.bin : raw binary image data
    - file_name_meta.json : metadata
    """

    # --- Initial setup ---
    HAMAMATSU = 'HamamatsuHam_DCAM'
    circ_buff_size_mb = 32000
    mmc.setConfig('Channel', config)
    mmc.waitForSystem()

    camera = mmc.getCameraDevice()
    interval_ms = float(mmc.getProperty(camera, 'Exposure'))
    interval_s = interval_ms / 1000.0

    # --- Check bit depth ---
    pixel_type = np.uint16
    bytes_per_pixel = mmc.getBytesPerPixel()
    if bytes_per_pixel == 1:
        pixel_type = np.uint8

    # --- Apply ROI if provided ---
    if ROI:
        x, y, w, h = ROI
        mmc.setROI(int(x), int(y), int(w), int(h))
        mmc.waitForSystem()
    else:
        w = mmc.getImageWidth()
        h = mmc.getImageHeight()

    nImages = ceil(runtime / interval_s)

    # --- Prepare output files ---
    bin_path = file_name + '.bin'
    meta_path = file_name + '_meta.json'
    if os.path.exists(bin_path):
        print(f"⚠️ File {bin_path} already exists — skipping acquisition.")
        return

    f = open(bin_path, 'wb')

    print(f"Recording {nImages} frames ({runtime:.1f}s at {1/interval_s:.2f} fps)")
    print(f"Saving to: {bin_path}")
    sys.stdout.flush()

    # --- Initialize circular buffer ---
    mmc.setCircularBufferMemoryFootprint(circ_buff_size_mb)
    mmc.initializeCircularBuffer()
    mmc.prepareSequenceAcquisition(camera)
    mmc.waitForSystem()
    mmc.startContinuousSequenceAcquisition(interval_ms)

    # --- Timing and counters ---
    t_detect = []
    dt_process = []
    dropped_frames = []

    print("Acquiring...", flush=True)
    t0 = time.time()
    frame_counter = 0

    try:
        while time.time() - t0 < runtime:
            if mmc.getRemainingImageCount() > 0:
                t1 = time.time()
                img = mmc.getLastImage()
                rem = mmc.getRemainingImageCount()
                if rem > 1:
                    dropped_frames.append(rem - 1)
                mmc.clearCircularBuffer()

                # Convert to array
                img = np.asarray(img, dtype=pixel_type)
                img = img.reshape((h, w))

                # Optional 8-bit conversion
                if bit8 and bytes_per_pixel > 1:
                    img = (img / 256).astype(np.uint8)

                # Write binary image
                img.tofile(f)

                t_detect.append(time.time() - t0)
                dt_process.append(time.time() - t1)
                frame_counter += 1

    except KeyboardInterrupt:
        print("Acquisition interrupted by user.")
    finally:
        # --- Cleanup ---
        mmc.stopSequenceAcquisition()
        mmc.waitForSystem()
        mmc.clearCircularBuffer()
        mmc.clearROI()
        f.close()

        print(f"Saved {frame_counter} frames.")
        print(f"Dropped frames (detected): {sum(dropped_frames)}")

        # --- Write metadata ---
        meta = {
            'Config': config,
            'Runtime_sec': runtime,
            'Exposure_ms': interval_ms,
            'Frames_Requested': nImages,
            'Frames_Saved': frame_counter,
            'Dropped_Frames': int(sum(dropped_frames)),
            'Resolution': {'Width': w, 'Height': h},
            'BitDepth': 8 if bit8 else bytes_per_pixel * 8,
            'Timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            't_detect': t_detect,
            'dt_process': dt_process
        }

        with open(meta_path, 'w') as mf:
            json.dump(meta, mf, indent=2)

        print(f"Metadata saved to: {meta_path}")
        print("✅ Acquisition complete.")
        
        
# code to use the functions        
mmc = initialize()

mmc.setConfig('lamp','on')
live(mmc,'tr_40x_20fps')
mmc.setConfig('lamp','off')

img = takePicture(mmc,'tr_10x_20fps')
sequenceAcquisition(mmc, "D:/tests/test", 30, 'tr_40x_100fps')