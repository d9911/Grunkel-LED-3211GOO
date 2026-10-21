// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;
import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.WindowManager;
public final class PhotoPreviewActivity extends Activity {
    private PhotoShow show;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state); getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN | WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        show = new PhotoShow(this, this::finish, true); setContentView(show.view);
    }
    private boolean previewKey(int code) {
        return code == KeyEvent.KEYCODE_DPAD_LEFT || code == KeyEvent.KEYCODE_DPAD_RIGHT || code == KeyEvent.KEYCODE_DPAD_CENTER
            || code == KeyEvent.KEYCODE_ENTER || code == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE || code == KeyEvent.KEYCODE_SPACE;
    }
    @Override public boolean onKeyDown(int code, KeyEvent event) {
        if (previewKey(code)) {
            if (event.getRepeatCount() == 0) {
                if (code == KeyEvent.KEYCODE_DPAD_LEFT) show.step(-1);
                else if (code == KeyEvent.KEYCODE_DPAD_RIGHT) show.step(1);
                else show.togglePaused();
            }
            return true;
        }
        if (code == KeyEvent.KEYCODE_ESCAPE || code == KeyEvent.KEYCODE_MEDIA_STOP) { finish(); return true; }
        return super.onKeyDown(code, event);
    }
    @Override public boolean onKeyUp(int code, KeyEvent event) {
        // Consume the OK release that opened preview, without immediately closing or pausing it.
        return previewKey(code) || super.onKeyUp(code, event);
    }
    @Override protected void onDestroy() { if (show != null) show.close(); super.onDestroy(); }
}
