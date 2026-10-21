// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.File;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public final class MainActivity extends Activity {
    private static final int HOME = 0, DRIVES = 1, FOLDER = 2;
    private JSONObject words;
    private LinearLayout list;
    private File browsing, root;
    private int screen = HOME;
    private boolean wantsFolder, watchingStorage;
    private final BroadcastReceiver storage = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            // Refresh only this visible picker; no background monitor or USB writes.
            if (screen == HOME) home(false);
            else if (screen == DRIVES || browsing == null || !browsing.isDirectory()) volumes();
            else folder(browsing);
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state); words = PhotoData.strings(this); home(false);
    }
    private String text(String key) { return PhotoData.text(words, key); }
    private void page(String title, String detail, boolean folders) {
        LinearLayout shell = new LinearLayout(this); shell.setOrientation(LinearLayout.VERTICAL);
        shell.setBackgroundColor(Color.rgb(18, 22, 26)); shell.setPadding(48, 24, 48, 16);
        TextView heading = new TextView(this); heading.setText(title); heading.setTextColor(Color.WHITE); heading.setTextSize(25); shell.addView(heading);
        TextView body = new TextView(this); body.setText(detail); body.setTextColor(Color.LTGRAY); body.setTextSize(17); body.setPadding(0, 8, 0, 12); shell.addView(body);
        ScrollView scroll = new ScrollView(this); list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list); shell.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        TextView help = new TextView(this); help.setText(text(folders ? "folder_navigation" : "navigation"));
        help.setTextColor(Color.LTGRAY); help.setTextSize(15); help.setPadding(0, 12, 0, 0); shell.addView(help); setContentView(shell);
    }
    private Button button(String label, boolean enabled, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setTextSize(18); b.setAllCaps(false); b.setEnabled(enabled);
        b.setOnClickListener(v -> action.run()); list.addView(b, new LinearLayout.LayoutParams(-1, 60)); return b;
    }
    private String location(File folder, File volume) {
        String relative = folder.equals(volume) ? "" : folder.getAbsolutePath().substring(volume.getAbsolutePath().length());
        return "USB" + relative;
    }
    private void home(boolean saved) {
        screen = HOME; browsing = null;
        File selected = PhotoData.chosen(this);
        int count = PhotoData.hasAccess(this) ? PhotoData.images(selected).size() : 0;
        String path = text("no_folder");
        if (selected != null) for (File volume : PhotoData.roots(this)) if (PhotoData.inside(selected, volume)) { path = location(selected, volume); break; }
        String detail = text("info") + "\n" + path + (count > 0 ? " · " + count + " " + text("photos") : "");
        if (saved) detail += "\n" + text("saved");
        page(text("title"), detail, false);
        Button choose = button(text("choose"), true, () -> {
            if (!PhotoData.hasAccess(this)) { wantsFolder = true; requestPermissions(new String[]{PhotoData.permission()}, 7); }
            else volumes();
        });
        Button preview = button(text("preview"), count > 0, () -> startActivity(new Intent(this, PhotoPreviewActivity.class)));
        button(text("exit"), true, this::finish);
        if (saved && count > 0) preview.requestFocus(); else choose.requestFocus();
    }
    private void volumes() {
        screen = DRIVES; browsing = null;
        List<File> roots = PhotoData.roots(this);
        page(text("choose_drive"), roots.isEmpty() ? text("no_drive") : text("read_only"), false);
        int n = 0;
        for (File volume : roots) {
            final File selected = volume;
            Button b = button("USB " + (++n), true, () -> { root = selected; folder(selected); });
            if (n == 1) b.requestFocus();
        }
        Button back = button(text("back"), true, () -> home(false));
        if (roots.isEmpty()) back.requestFocus();
    }
    private void folder(File dir) {
        if (root == null || !PhotoData.inside(dir, root) || !dir.isDirectory()) { volumes(); return; }
        screen = FOLDER; browsing = dir;
        int count = PhotoData.images(dir).size();
        page(location(dir, root), count + " " + text("photos") + " · " + text("folder_only"), true);
        Button use = button(text("use_folder"), count > 0, () -> {
            getSharedPreferences(PhotoData.PREFS, MODE_PRIVATE).edit().putString("folder", dir.getAbsolutePath()).apply(); home(true);
        });
        Button back = button(text("back"), true, this::parent);
        File[] entries = dir.listFiles(File::isDirectory);
        int shown = 0;
        if (entries != null) {
            Arrays.sort(entries, Comparator.comparing(File::getName, String.CASE_INSENSITIVE_ORDER));
            for (File entry : entries) {
                if (entry.getName().startsWith(".") || !PhotoData.inside(entry, root)) continue;
                final File next = entry;
                Button b = button(entry.getName(), true, () -> folder(next));
                if (shown++ == 0 && count == 0) b.requestFocus();
                if (shown == 200) break;
            }
        }
        if (count > 0) use.requestFocus(); else if (shown == 0) back.requestFocus();
    }
    private void parent() { if (browsing == null || browsing.equals(root)) volumes(); else folder(browsing.getParentFile()); }
    @Override public void onBackPressed() {
        if (screen == FOLDER) parent(); else if (screen == DRIVES) home(false); else finish();
    }
    @Override public boolean onKeyDown(int code, KeyEvent event) {
        if (code == KeyEvent.KEYCODE_DPAD_LEFT && screen == FOLDER) { if (event.getRepeatCount() == 0) parent(); return true; }
        if (code == KeyEvent.KEYCODE_ESCAPE) { finish(); return true; }
        return super.onKeyDown(code, event);
    }
    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request, permissions, results);
        if (request == 7) { wantsFolder = false; if (PhotoData.hasAccess(this)) volumes(); else home(false); }
    }
    @Override protected void onResume() {
        super.onResume(); words = PhotoData.strings(this);
        if (!wantsFolder) { if (screen == FOLDER) folder(browsing); else if (screen == DRIVES) volumes(); else home(false); }
        IntentFilter f = new IntentFilter(); f.addDataScheme("file");
        f.addAction(Intent.ACTION_MEDIA_MOUNTED); f.addAction(Intent.ACTION_MEDIA_UNMOUNTED);
        f.addAction(Intent.ACTION_MEDIA_REMOVED); f.addAction(Intent.ACTION_MEDIA_BAD_REMOVAL);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(storage, f, Context.RECEIVER_NOT_EXPORTED); else registerReceiver(storage, f);
        watchingStorage = true;
    }
    @Override protected void onPause() { if (watchingStorage) { unregisterReceiver(storage); watchingStorage = false; } super.onPause(); }
}
