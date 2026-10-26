package com.example.activity;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ReminderAlarmReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "activity_reminders_alarm";
    private static final String LOG_FILE = "alarm-debug.log";

    private static synchronized void logEvent(Context context, String message, Throwable error) {
        String time = new SimpleDateFormat(
                "yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()
        ).format(new Date());

        StringBuilder entry = new StringBuilder()
                .append("\n[").append(time).append("] ")
                .append(message).append("\n");

        if (error != null) {
            StringWriter stack = new StringWriter();
            error.printStackTrace(new PrintWriter(stack));
            entry.append(stack);
        }

        try (FileOutputStream out = new FileOutputStream(
                new File(context.getFilesDir(), LOG_FILE), true)) {
            out.write(entry.toString().getBytes("UTF-8"));
            out.flush();
        } catch (Throwable logError) {
            Log.e("ActivityAlarm", "Nie można zapisać alarm-debug.log", logError);
        }

        if (error != null) {
            Log.e("ActivityAlarm", message, error);
        } else {
            Log.i("ActivityAlarm", message);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        String alarmId = intent == null ? null : intent.getStringExtra("alarm_id");
        logEvent(context, "RECEIVER START; alarm_id=" + alarmId, null);

        try {
            if (intent == null) {
                throw new IllegalArgumentException("Odebrano pusty Intent alarmu");
            }

            String title = intent.getStringExtra("title");
            String body = intent.getStringExtra("body");
            if (title == null || title.isEmpty()) title = "Przypomnienie o aktywności";
            if (body == null || body.isEmpty()) body = "Nadchodzi zaplanowana aktywność";

            logEvent(context, "DANE ALARMU; title=" + title + "; body=" + body, null);

            NotificationManager manager =
                    (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager == null) {
                throw new IllegalStateException("NotificationManager jest null");
            }

            Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
            if (sound == null) {
                sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            }

            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel channel = new NotificationChannel(
                        CHANNEL_ID, "Alarmy aktywności",
                        NotificationManager.IMPORTANCE_HIGH);
                channel.setDescription("Dźwiękowe przypomnienia o zaplanowanych aktywnościach");
                channel.enableVibration(true);
                channel.setSound(sound, new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build());
                manager.createNotificationChannel(channel);
                logEvent(context, "KANAŁ POWIADOMIEŃ UTWORZONY", null);
            }

            Intent open = context.getPackageManager()
                    .getLaunchIntentForPackage(context.getPackageName());
            PendingIntent contentIntent = null;
            if (open != null) {
                contentIntent = PendingIntent.getActivity(
                        context, 901, open,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            }

            Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                    ? new Notification.Builder(context, CHANNEL_ID)
                    : new Notification.Builder(context);

            builder.setSmallIcon(context.getResources().getIdentifier("ic_notification", "drawable", context.getPackageName()))
                    .setContentTitle(title)
                    .setContentText(body)
                    .setStyle(new Notification.BigTextStyle().bigText(body))
                    .setCategory(Notification.CATEGORY_ALARM)
                    .setPriority(Notification.PRIORITY_MAX)
                    .setAutoCancel(true);

            if (contentIntent != null) builder.setContentIntent(contentIntent);

            if (Build.VERSION.SDK_INT < 26) {
                builder.setSound(sound);
                builder.setVibrate(new long[]{0, 500, 250, 500, 250, 700});
            }

            int notificationId = alarmId == null
                    ? (int) System.currentTimeMillis() : alarmId.hashCode();

            Notification notification = builder.build();
            logEvent(context, "NOTIFICATION BUILD OK; id=" + notificationId, null);
            manager.notify(notificationId, notification);
            logEvent(context, "NOTIFICATION OK; id=" + notificationId, null);

        } catch (Throwable error) {
            logEvent(context, "EXCEPTION podczas obsługi alarmu; alarm_id=" + alarmId,
                    error);
        } finally {
            logEvent(context, "RECEIVER END; alarm_id=" + alarmId, null);
        }
    }
}
