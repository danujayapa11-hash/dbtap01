from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import platform

if platform == "android":
    from android import activity as _unused  # noqa: F401
    from jnius import autoclass, cast

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Context = autoclass("android.content.Context")
    Intent = autoclass("android.content.Intent")
    ComponentName = autoclass("android.content.ComponentName")
    DPM = autoclass("android.app.admin.DevicePolicyManager")
    PowerManager = autoclass("android.os.PowerManager")

    PKG = "org.example.doubletap"

    def _activity():
        return PythonActivity.mActivity

    def _admin_component():
        return ComponentName(PKG, PKG + ".AdminReceiver")

    def _dpm():
        return cast(DPM, _activity().getSystemService(Context.DEVICE_POLICY_SERVICE))

    def is_admin():
        return _dpm().isAdminActive(_admin_component())

    def request_admin():
        intent = Intent(DPM.ACTION_ADD_DEVICE_ADMIN)
        intent.putExtra(DPM.EXTRA_DEVICE_ADMIN,
                        cast("android.os.Parcelable", _admin_component()))
        intent.putExtra(DPM.EXTRA_ADD_EXPLANATION,
                        "Needed so a double tap can lock your screen.")
        _activity().startActivity(intent)

    def lock_screen():
        if is_admin():
            _dpm().lockNow()
            return True
        request_admin()
        return False

    def wake_screen(ms=5000):
        pm = cast(PowerManager, _activity().getSystemService(Context.POWER_SERVICE))
        flags = (PowerManager.FULL_WAKE_LOCK
                 | PowerManager.ACQUIRE_CAUSES_WAKEUP
                 | PowerManager.ON_AFTER_RELEASE)
        wl = pm.newWakeLock(flags, "doubletap:wake")
        wl.acquire(ms)
else:
    def is_admin(): return False
    def request_admin(): print("request_admin (desktop stub)")
    def lock_screen(): print("lock_screen (desktop stub)"); return True
    def wake_screen(ms=5000): print("wake_screen (desktop stub)")


class TapArea(Label):
    """Big area: double tap anywhere in it to lock the screen."""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            lock_screen()
            return True
        return super().on_touch_down(touch)


class DoubleTapLockApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=12)
        self.status = Label(size_hint_y=None, height=60)
        root.add_widget(self.status)
        root.add_widget(TapArea(text="Double tap here\nto turn the screen OFF",
                                halign="center", font_size="22sp"))
        b1 = Button(text="Grant permission (Device Admin)",
                    size_hint_y=None, height=120)
        b1.bind(on_release=lambda *_: request_admin())
        b2 = Button(text="Test: lock, then wake in 10 s",
                    size_hint_y=None, height=120)
        b2.bind(on_release=self.lock_then_wake)
        root.add_widget(b1)
        root.add_widget(b2)
        Clock.schedule_interval(self.refresh, 1)
        return root

    def refresh(self, *_):
        self.status.text = ("Permission: GRANTED" if is_admin()
                            else "Permission: NOT granted")

    def lock_then_wake(self, *_):
        if lock_screen():
            Clock.schedule_once(lambda dt: wake_screen(), 10)

    def on_resume(self):
        return True

    def on_pause(self):
        return True  # keep app alive when screen locks (needed for the timer)


if __name__ == "__main__":
    DoubleTapLockApp().run()
