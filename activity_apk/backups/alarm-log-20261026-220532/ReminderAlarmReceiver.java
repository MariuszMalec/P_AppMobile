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

public class ReminderAlarmReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "activity_reminders_alarm";

    @Override
    public void onReceive(Context context, Intent intent) {
        String title = intent.getStringExtra("title");
        String body = intent.getStringExtra("body");
        if (title == null || title.isEmpty()) title = "Przypomnienie o aktywności";
        if (body == null || body.isEmpty()) body = "Nadchodzi zaplanowana aktywność";

        NotificationManager manager =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);

        Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        if (sound == null) sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);

        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Alarmy aktywności", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Dźwiękowe przypomnienia o zaplanowanych aktywnościach");
            channel.enableVibration(true);
            channel.setSound(sound, new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build());
            manager.createNotificationChannel(channel);
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

        builder.setSmallIcon(context.getApplicationInfo().icon)
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

        String alarmId = intent.getStringExtra("alarm_id");
        int notificationId = alarmId == null ? (int) System.currentTimeMillis() : alarmId.hashCode();
        manager.notify(notificationId, builder.build());
    }
}
