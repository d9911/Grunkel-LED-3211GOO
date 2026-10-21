// Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
package org.d9911.grunkel.photos;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Environment;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import org.json.JSONObject;
import java.io.File;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

final class PhotoData {
    static final int INTERVAL_MS = 30000;
    static final String PREFS = "photos";
    static String permission() {
        return Build.VERSION.SDK_INT >= 33 ? "android.permission.READ_MEDIA_IMAGES" : "android.permission.READ_EXTERNAL_STORAGE";
    }
    static boolean hasAccess(Context c) {
        return c.checkSelfPermission(permission()) == PackageManager.PERMISSION_GRANTED;
    }
    static List<File> roots(Context c) {
        List<File> result = new ArrayList<>();
        StorageManager sm = (StorageManager)c.getSystemService(Context.STORAGE_SERVICE);
        for (StorageVolume v : sm.getStorageVolumes()) {
            if (!v.isRemovable() || !(Environment.MEDIA_MOUNTED.equals(v.getState()) || Environment.MEDIA_MOUNTED_READ_ONLY.equals(v.getState()))) continue;
            File root = Build.VERSION.SDK_INT >= 30 ? v.getDirectory() : (v.getUuid() == null ? null : new File("/storage/" + v.getUuid()));
            if (root != null && root.isDirectory()) result.add(root);
        }
        Collections.sort(result, (a, b) -> a.getPath().compareTo(b.getPath()));
        return result;
    }
    static boolean inside(File file, File root) {
        try {
            String p = file.getCanonicalPath(), base = root.getCanonicalPath();
            return p.equals(base) || p.startsWith(base + File.separator);
        } catch (Exception e) { return false; }
    }
    static File chosen(Context c) {
        String path = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("folder", "");
        if (path.isEmpty()) return null;
        File folder = new File(path);
        for (File root : roots(c)) if (inside(folder, root) && folder.isDirectory()) return folder;
        return null;
    }
    static List<File> images(File folder) {
        List<File> result = new ArrayList<>();
        if (folder == null) return result;
        File[] entries = folder.listFiles();
        if (entries == null) return result;
        for (File f : entries) {
            String n = f.getName().toLowerCase(Locale.ROOT);
            if (!n.startsWith(".") && f.isFile() && inside(f, folder) && (n.endsWith(".jpg") || n.endsWith(".jpeg") || n.endsWith(".png") || n.endsWith(".webp") || n.endsWith(".heic") || n.endsWith(".heif"))) result.add(f);
        }
        Collections.sort(result, (a, b) -> a.getName().compareToIgnoreCase(b.getName()));
        return result.size() > 1000 ? new ArrayList<>(result.subList(0, 1000)) : result;
    }
    static JSONObject status(Context c) {
        JSONObject result = new JSONObject();
        try {
            File folder = chosen(c);
            int count = hasAccess(c) ? images(folder).size() : 0;
            result.put("folder_selected", !c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("folder", "").isEmpty());
            result.put("photo_access_granted", hasAccess(c));
            result.put("drive_available", folder != null);
            result.put("image_candidates", count);
            result.put("can_preview", count > 0);
            result.put("interval_ms", INTERVAL_MS);
            result.put("network_permission_declared", false);
        } catch (Exception e) { /* fixed keys only; never emit paths/filenames */ }
        return result;
    }
    static JSONObject strings(Context c) {
        String lang = Locale.getDefault().getLanguage();
        if (!lang.equals("ru") && !lang.equals("es")) lang = "en";
        try (InputStream stream = c.getAssets().open("locales/" + lang + ".json")) {
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[2048]; int n;
            while ((n = stream.read(buf)) != -1) out.write(buf, 0, n);
            return new JSONObject(out.toString("UTF-8"));
        } catch (Exception e) { return new JSONObject(); }
    }
    static String text(JSONObject strings, String key) { return strings.optString(key, key); }
}
