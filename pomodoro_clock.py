import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import winsound
from datetime import datetime


class PomodoroClock:
    def __init__(self):
        self.work_minutes = 25
        self.short_break_minutes = 5
        self.long_break_minutes = 15
        self.rounds_before_long = 4

        self.state = "idle"  # idle, running, paused
        self.phase = "work"  # work, short_break, long_break
        self.time_left = self.work_minutes * 60
        self.round_count = 0
        self.total_pomodoros_today = 0

        self._job_id = None  # 用于取消 tkinter.after
        self._stats_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pomodoro_stats.json"
        )

        self._load_stats()

        # 颜色方案 — 灵感来源：《间谍过家家》草地场景
        # 柔和自然风：草绿 + 淡粉 + 柔蓝
        self.bg_color = "#F0F7EC"       # 淡绿底（草地氛围）
        self.colors = {
            "work": "#6BBF6E",          # 草地绿（工作中）
            "short_break": "#E8A0BF",   # 小花粉（短休息）
            "long_break": "#87B5D6",    # 柔蓝（长休息，条纹衬衫色）
            "idle": "#4A5568",          # 深灰褐（空闲）
        }
        # 按钮配色
        self.btn_colors = {
            "start": "#6BBF6E",
            "pause": "#E8A0BF",
            "skip": "#87B5D6",
            "continue": "#87B5D6",
            "save": "#6BBF6E",
        }

        # --- 主窗口 ---
        self.root = tk.Tk()
        self.root.title("番茄钟")
        self.root.geometry("400x450")
        self.root.resizable(False, False)
        self.root.configure(bg=self.bg_color)

        self._build_ui()
        self._update_display()
        self._tick()  # 启动计时循环

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        # 阶段标签
        self.label_phase = tk.Label(
            self.root, text="准备开始", font=("Helvetica", 18), fg="#8E99A4",
            bg=self.bg_color,
        )
        self.label_phase.pack(pady=(30, 5))

        # 倒计时大字
        self.label_time = tk.Label(
            self.root, text="25:00", font=("Helvetica", 72, "bold"), fg="#4A5568",
            bg=self.bg_color,
        )
        self.label_time.pack(pady=10)

        # 轮次显示
        self.label_round = tk.Label(
            self.root,
            text=f"第 1 / {self.rounds_before_long} 个番茄",
            font=("Helvetica", 12),
            fg="#A0AEC0",
            bg=self.bg_color,
        )
        self.label_round.pack(pady=(0, 10))

        # 控制按钮
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(
            btn_frame,
            text="开始",
            width=8,
            font=("Helvetica", 12),
            command=self._on_start,
            bg=self.btn_colors["start"],
            fg="white",
            activebackground="#5AAF5D",
        )
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_pause = tk.Button(
            btn_frame,
            text="暂停",
            width=8,
            font=("Helvetica", 12),
            command=self._on_pause,
            bg=self.btn_colors["pause"],
            fg="white",
            activebackground="#D4909F",
            state="disabled",
        )
        self.btn_pause.grid(row=0, column=1, padx=5)

        self.btn_skip = tk.Button(
            btn_frame,
            text="跳过",
            width=8,
            font=("Helvetica", 12),
            command=self._on_skip,
            bg=self.btn_colors["skip"],
            fg="white",
            activebackground="#76A5C6",
            state="disabled",
        )
        self.btn_skip.grid(row=0, column=2, padx=5)

        # 底部功能按钮
        bottom_frame = tk.Frame(self.root, bg=self.bg_color)
        bottom_frame.pack(pady=(10, 5))

        tk.Button(
            bottom_frame,
            text="设置",
            width=10,
            command=self._open_settings,
            bg=self.btn_colors["skip"],
            fg="white",
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            bottom_frame,
            text="今日统计",
            width=10,
            command=self._open_stats,
            bg=self.btn_colors["pause"],
            fg="white",
        ).grid(row=0, column=1, padx=5)

        # 今日番茄数小标签
        self.label_today = tk.Label(
            self.root,
            text=f"今日完成: {self.total_pomodoros_today} 个番茄",
            font=("Helvetica", 10),
            fg="#A0AEC0",
            bg=self.bg_color,
        )
        self.label_today.pack(pady=(5, 0))

    # ------------------------------------------------------------------
    # 计时核心
    # ------------------------------------------------------------------
    def _tick(self):
        """每秒刷新一次，驱动倒计时"""
        if self.state == "running" and self.time_left > 0:
            self.time_left -= 1
            self._update_display()
        elif self.state == "running" and self.time_left <= 0:
            self._on_phase_complete()
        # 每 1000ms 调度下一次
        self._job_id = self.root.after(1000, self._tick)

    def _update_display(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        self.label_time.config(text=f"{mins:02d}:{secs:02d}")

        color = self.colors[self.phase] if self.state != "idle" else self.colors["idle"]
        self.label_time.config(fg=color)

        phase_text = {
            "work": "工作中",
            "short_break": "短休息",
            "long_break": "长休息",
            "idle": "准备开始",
        }
        self.label_phase.config(text=phase_text[self.phase])
        self.label_phase.config(fg=color)

        if self.phase == "work":
            self.label_round.config(
                text=f"第 {self.round_count + 1} / {self.rounds_before_long} 个番茄"
            )

    # ------------------------------------------------------------------
    # 按钮回调
    # ------------------------------------------------------------------
    def _on_start(self):
        if self.state == "idle":
            self.state = "running"
            self._reset_phase()
        elif self.state == "paused":
            self.state = "running"
        self._update_buttons()

    def _on_pause(self):
        if self.state == "running":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "running"
        self._update_buttons()

    def _on_skip(self):
        """跳过当前阶段，直接进入下一阶段"""
        self._advance_phase()
        self.state = "running"
        self._update_buttons()

    def _update_buttons(self):
        if self.state == "idle":
            self.btn_start.config(text="开始", bg=self.btn_colors["start"], state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_skip.config(state="disabled")
        elif self.state == "running":
            self.btn_start.config(state="disabled")
            self.btn_pause.config(text="暂停", bg=self.btn_colors["pause"], state="normal")
            self.btn_skip.config(state="normal")
        elif self.state == "paused":
            self.btn_start.config(text="继续", bg=self.btn_colors["continue"], state="normal")
            self.btn_pause.config(text="继续", bg=self.btn_colors["pause"], state="normal")
            self.btn_skip.config(state="normal")

    # ------------------------------------------------------------------
    # 阶段管理
    # ------------------------------------------------------------------
    def _reset_phase(self):
        """重置当前阶段的时间"""
        if self.phase == "work":
            self.time_left = self.work_minutes * 60
        elif self.phase == "short_break":
            self.time_left = self.short_break_minutes * 60
        elif self.phase == "long_break":
            self.time_left = self.long_break_minutes * 60

    def _on_phase_complete(self):
        """当前阶段结束时触发"""
        self._play_sound()

        if self.phase == "work":
            self.round_count += 1
            self.total_pomodoros_today += 1
            self._save_stats()
            self.label_today.config(
                text=f"今日完成: {self.total_pomodoros_today} 个番茄"
            )

            if self.round_count >= self.rounds_before_long:
                self.round_count = 0
                self.phase = "long_break"
                messagebox.showinfo("番茄钟", "太棒了！完成一轮，享受长休息吧 🎉")
            else:
                self.phase = "short_break"
                messagebox.showinfo("番茄钟", "干得好！休息一下吧 ☕")
        else:
            self.phase = "work"
            messagebox.showinfo("番茄钟", "休息结束，开始新的番茄吧 💪")

        self._reset_phase()
        self._update_display()
        # 自动开始下一阶段
        self.state = "running"
        self._update_buttons()

    def _advance_phase(self):
        """手动跳过，直接进入下一阶段逻辑"""
        if self.phase == "work":
            self.round_count += 1
            self.total_pomodoros_today += 1
            self._save_stats()
            self.label_today.config(
                text=f"今日完成: {self.total_pomodoros_today} 个番茄"
            )

            if self.round_count >= self.rounds_before_long:
                self.round_count = 0
                self.phase = "long_break"
            else:
                self.phase = "short_break"
        else:
            self.phase = "work"

        self._reset_phase()
        self._update_display()

    # ------------------------------------------------------------------
    # 提示音
    # ------------------------------------------------------------------
    def _play_sound(self):
        """播放系统提示音（Windows Beep）"""
        try:
            winsound.Beep(1000, 500)  # 1000Hz, 500ms
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 统计持久化
    # ------------------------------------------------------------------
    def _load_stats(self):
        """从 JSON 加载今日统计"""
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entry = data.get(today, {})
                self.total_pomodoros_today = entry.get("count", 0)
            else:
                self.total_pomodoros_today = 0
        except (json.JSONDecodeError, IOError):
            self.total_pomodoros_today = 0

    def _save_stats(self):
        """保存统计到 JSON"""
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
            data[today] = {
                "count": self.total_pomodoros_today,
                "minutes": self.total_pomodoros_today * self.work_minutes,
            }
            with open(self._stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    # ------------------------------------------------------------------
    # 设置窗口
    # ------------------------------------------------------------------
    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("300x280")
        win.resizable(False, False)
        win.configure(bg=self.bg_color)

        tk.Label(win, text="工作时长（分钟）", font=("Helvetica", 11),
                 bg=self.bg_color).pack(pady=(20, 2))
        var_work = tk.IntVar(value=self.work_minutes)
        ttk.Spinbox(win, from_=1, to=120, textvariable=var_work, width=8).pack()

        tk.Label(win, text="短休息时长（分钟）", font=("Helvetica", 11),
                 bg=self.bg_color).pack(pady=(15, 2))
        var_short = tk.IntVar(value=self.short_break_minutes)
        ttk.Spinbox(win, from_=1, to=30, textvariable=var_short, width=8).pack()

        tk.Label(win, text="长休息时长（分钟）", font=("Helvetica", 11),
                 bg=self.bg_color).pack(pady=(15, 2))
        var_long = tk.IntVar(value=self.long_break_minutes)
        ttk.Spinbox(win, from_=1, to=60, textvariable=var_long, width=8).pack()

        def on_save():
            self.work_minutes = var_work.get()
            self.short_break_minutes = var_short.get()
            self.long_break_minutes = var_long.get()
            if self.state == "idle":
                self._reset_phase()
                self._update_display()
            win.destroy()

        tk.Button(
            win, text="保存", width=12, command=on_save,
            bg=self.btn_colors["save"], fg="white",
        ).pack(pady=20)

    # ------------------------------------------------------------------
    # 统计窗口
    # ------------------------------------------------------------------
    def _open_stats(self):
        win = tk.Toplevel(self.root)
        win.title("今日统计")
        win.geometry("300x250")
        win.resizable(False, False)
        win.configure(bg=self.bg_color)

        today = datetime.now().strftime("%Y-%m-%d")

        tk.Label(
            win, text=f" {today}", font=("Helvetica", 14, "bold"),
            bg=self.bg_color,
        ).pack(pady=(20, 10))

        tk.Label(
            win,
            text=f"完成番茄: {self.total_pomodoros_today} 个",
            font=("Helvetica", 12),
            bg=self.bg_color,
        ).pack(pady=5)

        tk.Label(
            win,
            text=f"专注时长: {self.total_pomodoros_today * self.work_minutes} 分钟",
            font=("Helvetica", 12),
            bg=self.bg_color,
        ).pack(pady=5)

        # 显示最近 7 天
        tk.Label(
            win, text="── 最近 7 天 ──", font=("Helvetica", 11),
            bg=self.bg_color,
        ).pack(pady=(15, 5))

        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                dates = sorted(data.keys(), reverse=True)[:7]
                for d in dates:
                    c = data[d].get("count", 0)
                    m = data[d].get("minutes", 0)
                    tk.Label(
                        win, text=f"{d}: {c} 个番茄 ({m} 分钟)",
                        font=("Helvetica", 10), bg=self.bg_color,
                    ).pack()
        except (json.JSONDecodeError, IOError):
            pass

    # ------------------------------------------------------------------
    # 运行
    # ------------------------------------------------------------------
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PomodoroClock()
    app.run()
