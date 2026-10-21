// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.ImageDecoder;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

final class PhotoShow {
    final FrameLayout view;
    private final ImageView image;
    private final TextView clock, message, controls;
    private final Context context;
    private final List<File> files;
    private final Set<Integer> unreadable = new HashSet<>(); // used only on the decoder thread
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService decoder = Executors.newSingleThreadExecutor();
    private final Runnable failed;
    private volatile boolean stopped;
    private int currentIndex = -1, generation;
    private final Runnable advance = () -> load(currentIndex + 1, 1);
    private boolean paused;
    PhotoShow(Context c, Runnable onFailure, boolean preview) {
        context = c; failed = onFailure;
        files = PhotoData.hasAccess(c) ? PhotoData.images(PhotoData.chosen(c)) : java.util.Collections.emptyList();
        view = new FrameLayout(c); view.setBackgroundColor(Color.BLACK);
        image = new ImageView(c); image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        view.addView(image, new FrameLayout.LayoutParams(-1, -1));
        clock = new TextView(c); clock.setTextColor(Color.WHITE); clock.setTextSize(20); clock.setShadowLayer(4, 1, 1, Color.BLACK); clock.setGravity(Gravity.RIGHT);
        FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.RIGHT); cp.setMargins(24, 20, 28, 20); view.addView(clock, cp);
        message = new TextView(c); message.setTextColor(Color.WHITE); message.setTextSize(22); message.setGravity(Gravity.CENTER);
        view.addView(message, new FrameLayout.LayoutParams(-1, -1));
        controls = new TextView(c); controls.setTextColor(Color.WHITE); controls.setTextSize(16); controls.setShadowLayer(4, 1, 1, Color.BLACK); controls.setGravity(Gravity.CENTER);
        FrameLayout.LayoutParams help = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM); help.setMargins(24, 12, 24, 20);
        if (preview) { view.addView(controls, help); updateControls(); }
        if (files.isEmpty()) unavailable(); else load(0, 1);
        updateClock();
    }
    private void updateClock() {
        if (stopped) return;
        clock.setText(new SimpleDateFormat("HH:mm\nEEE, dd.MM.yyyy", Locale.getDefault()).format(new Date()));
        handler.postDelayed(this::updateClock, 60000);
    }
    private void updateControls() {
        org.json.JSONObject words = PhotoData.strings(context);
        controls.setText((paused ? PhotoData.text(words, "paused") + " · " : "") + PhotoData.text(words, "preview_controls"));
    }
    void togglePaused() {
        if (stopped) return;
        paused = !paused; updateControls(); handler.removeCallbacks(advance);
        if (!paused && currentIndex >= 0) handler.postDelayed(advance, PhotoData.INTERVAL_MS);
    }
    void step(int direction) { if (!stopped) load(currentIndex < 0 ? 0 : currentIndex + direction, direction); }
    private void unavailable() {
        if (stopped) return;
        handler.removeCallbacks(advance); image.setImageDrawable(null);
        message.setText(PhotoData.text(PhotoData.strings(context), "no_images"));
        handler.postDelayed(() -> { if (!stopped) failed.run(); }, 2000);
    }
    private void load(int start, int direction) {
        if (stopped) return;
        handler.removeCallbacks(advance);
        if (files.isEmpty() || PhotoData.chosen(context) == null) { unavailable(); return; }
        final int request = ++generation;
        decoder.execute(() -> {
            Bitmap decoded = null; int found = -1;
            for (int tries = 0; tries < files.size() && !stopped; tries++) {
                int candidate = Math.floorMod(start + tries * direction, files.size());
                if (unreadable.contains(candidate)) continue;
                File f = files.get(candidate);
                try {
                    if (!f.isFile()) continue;
                    if (android.os.Build.VERSION.SDK_INT >= 28) {
                        decoded = ImageDecoder.decodeBitmap(ImageDecoder.createSource(f), (d, info, src) -> {
                            int w = info.getSize().getWidth(), h = info.getSize().getHeight();
                            float factor = Math.max(1f, Math.max(w / 1280f, h / 720f));
                            d.setTargetSize(Math.max(1, (int)(w / factor)), Math.max(1, (int)(h / factor)));
                            d.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);
                        });
                    } else {
                        android.graphics.BitmapFactory.Options options = new android.graphics.BitmapFactory.Options();
                        options.inJustDecodeBounds = true; android.graphics.BitmapFactory.decodeFile(f.getPath(), options);
                        int sample = 1; while (options.outWidth / sample > 1280 || options.outHeight / sample > 720) sample *= 2;
                        options.inJustDecodeBounds = false; options.inSampleSize = sample;
                        decoded = android.graphics.BitmapFactory.decodeFile(f.getPath(), options);
                    }
                    if (decoded != null) { found = candidate; break; }
                } catch (Exception | OutOfMemoryError e) { /* skip unsupported/corrupt images; never log a private filename */ }
                unreadable.add(candidate);
            }
            final Bitmap result = decoded; final int selected = found;
            handler.post(() -> {
                if (stopped || generation != request) { if (result != null) result.recycle(); return; }
                if (result == null) { unavailable(); return; }
                currentIndex = selected; message.setText(""); image.setImageBitmap(result);
                if (!paused) handler.postDelayed(advance, PhotoData.INTERVAL_MS);
            });
        });
    }
    void close() { stopped = true; generation++; handler.removeCallbacksAndMessages(null); decoder.shutdownNow(); image.setImageDrawable(null); }
}
