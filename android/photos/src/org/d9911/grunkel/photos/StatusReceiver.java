// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
public final class StatusReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (!"org.d9911.grunkel.photos.STATUS".equals(intent.getAction())) return;
        setResultCode(-1); setResultData(PhotoData.status(context).toString());
    }
}
