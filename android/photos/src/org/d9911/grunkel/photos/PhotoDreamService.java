// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;
import android.service.dreams.DreamService;
public final class PhotoDreamService extends DreamService {
    private PhotoShow show;
    @Override public void onAttachedToWindow() {
        super.onAttachedToWindow(); setInteractive(false); setFullscreen(true); setScreenBright(true);
        show = new PhotoShow(this, this::finish, false); setContentView(show.view);
    }
    @Override public void onDetachedFromWindow() { if (show != null) show.close(); super.onDetachedFromWindow(); }
}
