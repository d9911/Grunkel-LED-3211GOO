// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.shortcuts;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.media.tv.TvContract;
import android.media.tv.TvInputInfo;
import android.media.tv.TvInputManager;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Environment;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;


/** Two permission-free, offline entry points; native apps own all media and input handling. */
public final class MainActivity extends Activity {
    private static final String TV = "com.mediatek.wwtv.tvcenter";
    private static final String MEDIA = "com.mediatek.wwtv.mediaplayer";
    private static final String PHOTOS = "org.d9911.grunkel.photos";
    private static final String FINGERPRINT = "Grunkel/Grunkel_2K_ATV2/martin:14/UKNV.260602.001/15547440:user/release-keys";
    private boolean listening;
    private LinearLayout rows;
    private TextView state;
    private final BroadcastReceiver storage = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { if (isUsb()) renderUsb(); }
    };
    private String text(String key) {
        int id = getResources().getIdentifier(key, "string", getPackageName());
        return id == 0 ? key : getString(id);
    }
    private boolean isUsb() { return getPackageName().equals("org.d9911.grunkel.usb"); }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (!FINGERPRINT.equals(android.os.Build.FINGERPRINT)) {
            page(text("unsupported")); button(text("back"), true, this::finish); return;
        }
        if (isUsb()) renderUsb();
        else renderInputs();
    }
    @Override public void onStart() {
        super.onStart();
        if (!isUsb() || !FINGERPRINT.equals(android.os.Build.FINGERPRINT)) return;
        IntentFilter f = new IntentFilter();
        f.addAction(Intent.ACTION_MEDIA_MOUNTED); f.addAction(Intent.ACTION_MEDIA_UNMOUNTED);
        f.addAction(Intent.ACTION_MEDIA_EJECT); f.addAction(Intent.ACTION_MEDIA_REMOVED);
        f.addAction(Intent.ACTION_MEDIA_CHECKING); f.addAction(Intent.ACTION_MEDIA_BAD_REMOVAL);
        f.addDataScheme("file"); registerReceiver(storage, f, Context.RECEIVER_NOT_EXPORTED); listening = true;
    }
    @Override public void onResume() { super.onResume(); if (FINGERPRINT.equals(android.os.Build.FINGERPRINT)) { if (isUsb()) renderUsb(); else renderInputs(); } }
    @Override public void onStop() { if (listening) { unregisterReceiver(storage); listening = false; } super.onStop(); }
    private void page(String detail) {
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(48,32,48,24); root.setBackgroundColor(Color.rgb(17,25,29));
        TextView title = new TextView(this); title.setText(text("app_name")); title.setTextSize(28); title.setTextColor(Color.WHITE); root.addView(title);
        state = new TextView(this); state.setText(detail); state.setTextSize(19); state.setTextColor(Color.LTGRAY); state.setPadding(0,14,0,16); root.addView(state);
        ScrollView scroll = new ScrollView(this); rows = new LinearLayout(this); rows.setOrientation(LinearLayout.VERTICAL); scroll.addView(rows);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        TextView help = new TextView(this); help.setText(text("help")); help.setTextSize(16); help.setTextColor(Color.LTGRAY); root.addView(help); setContentView(root);
    }
    private Button button(String label, boolean enabled, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setAllCaps(false); b.setTextSize(19); b.setEnabled(enabled);
        b.setOnClickListener(v -> action.run()); rows.addView(b,new LinearLayout.LayoutParams(-1,66)); return b;
    }
    private List<StorageVolume> mounted() {
        List<StorageVolume> result = new ArrayList<>();
        StorageManager sm = (StorageManager)getSystemService(Context.STORAGE_SERVICE);
        if (sm != null) for (StorageVolume v : sm.getStorageVolumes()) {
            String s = v.getState();
            if (v.isRemovable() && (Environment.MEDIA_MOUNTED.equals(s) || Environment.MEDIA_MOUNTED_READ_ONLY.equals(s))) result.add(v);
        }
        return result;
    }
    private boolean available(String pkg) { return getPackageManager().getLeanbackLaunchIntentForPackage(pkg) != null; }
    private void open(String pkg) {
        if (mounted().isEmpty()) { renderUsb(); return; }
        Intent i = getPackageManager().getLeanbackLaunchIntentForPackage(pkg);
        if (i == null) { state.setText(text("media_error")); return; }
        try { startActivity(i); } catch (RuntimeException e) { state.setText(text("media_error")); }
    }
    private void selectInput(TvInputInfo input) {
        if (!input.isPassthroughInput()) return;
        Intent i = new Intent(Intent.ACTION_VIEW)
            .setDataAndType(TvContract.buildChannelUriForPassthroughInput(input.getId()), TvContract.Channels.CONTENT_ITEM_TYPE)
            .setPackage(TV);
        try { startActivity(i); }
        catch (RuntimeException e) { state.setText(text("inputs_error")); }
    }
    private void renderInputs() {
        page(text("inputs_hint"));
        TvInputManager manager = (TvInputManager)getSystemService(Context.TV_INPUT_SERVICE);
        List<TvInputInfo> inputs;
        try { inputs = manager == null ? new ArrayList<>() : manager.getTvInputList(); }
        catch (RuntimeException e) { state.setText(text("inputs_error")); button(text("back"),true,this::finish); return; }
        String[] ids = {".hdmi.HDMIInputService/HW5", ".hdmi.HDMIInputService/HW6", ".hdmi.HDMIInputService/HW7", ".composite.CompositeInputService/HW2"};
        String[] labels = {"HDMI 1", "HDMI 2", "HDMI 3", "AV"};
        Button first = null;
        for (int n = 0; n < ids.length; n++) {
            for (TvInputInfo info : inputs) {
                if (!info.isPassthroughInput() || !info.getId().equals("com.mediatek.tvinput/" + ids[n])) continue;
                String detail = text("input_unknown");
                try {
                    int status = manager.getInputState(info.getId());
                    detail = text(status == TvInputManager.INPUT_STATE_CONNECTED ? "input_connected" : status == TvInputManager.INPUT_STATE_DISCONNECTED ? "input_disconnected" : "input_standby");
                } catch (RuntimeException e) { /* unknown state remains explicit */ }
                final TvInputInfo selected = info;
                Button b = button(labels[n] + " · " + detail,true,() -> selectInput(selected));
                // Keep a disconnected input selectable: some devices report the state late.
                if (first == null) first = b;
            }
        }
        if (first == null) state.setText(text("inputs_error"));
        button(text("refresh"),true,this::renderInputs); button(text("back"),true,this::finish);
        if (first != null) first.requestFocus();
    }
    private void renderUsb() {
        List<StorageVolume> volumes = mounted(); boolean ready = !volumes.isEmpty();
        page(ready ? text("connected") + " · " + volumes.size() : text("absent"));
        Button browse = button(text("browse"), ready && available(MEDIA), () -> open(MEDIA));
        button(text("photos"), ready && available(PHOTOS), () -> open(PHOTOS));
        Button refresh = button(text("refresh"), true, this::renderUsb);
        button(text("back"),true,this::finish);
        if (ready && browse.isEnabled()) browse.requestFocus(); else refresh.requestFocus();
    }
}
