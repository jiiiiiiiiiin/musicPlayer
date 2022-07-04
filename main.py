from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QUrl, QTimer
from player import Ui_MainWindow
import requests
import time
import threading
import mkf
import ncm
import pyttsx3


app_id = "xxxx"
api_key = "xxxx"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.lineEdit.setText("刚刚好")
        self.player = QMediaPlayer()

        self.search_result = None
        self.song_index = 0
        # 将按钮绑定到搜索
        self.ui.pushButton.clicked.connect(self.btn_search)
        # listWidget的按钮绑定到获取歌曲
        self.ui.listWidget.doubleClicked.connect(self.btn_get_song)
        # 播放按钮绑定到播放
        self.ui.pushButton_play.clicked.connect(self.play)
        self.ui.pushButton_stop.clicked.connect(self.stop)
        # plainTextEdit 禁止编辑
        self.ui.plainTextEdit.setReadOnly(True)
        # horizontalSlider 绑定到播放器
        self.ui.horizontalSlider.sliderMoved.connect(self.player.setPosition)
        self.ui.pushButton_next.clicked.connect(lambda: self.play("next"))
        self.ui.pushButton_last.clicked.connect(lambda: self.play("last"))

        # 创建定时器
        self.timer = QTimer()
        # 定时器绑定到更新时间
        self.timer.timeout.connect(self.update_time)

        # new一个语音识别线程
        self.thread = threading.Thread(target=self.voice_recognition)
        self.thread.start()
        self.order_list = []
        self.ui.listWidget_2.addItem("语音识别线程已启动")

        # 创建一个定时器，每隔0.3秒检查一次语音识别线程
        self.timer_2 = QTimer()
        self.timer_2.timeout.connect(self.check_voice_recognition)
        self.timer_2.start(300)

        self.pp = pyttsx3.init()

        self.current_song = None
        self.flag_play = False

    def voice_recognition(self):
        client = mkf.Client(app_id, api_key)
        client.recv_result_analysis = self.handle_order
        client.send()

    def check_voice_recognition(self):
        if not self.order_list:
            return

        if time.time() - self.order_list[-1].get("time") > 0.3:
            order = self.order_list[-1]
            self.order_list = []
            # 去除所有的标点符号
            order_str = order.get("order").replace("，", "").replace("。", "").replace("？", "").replace("！", "")
            order["order"] = order_str

            flag_in = False
            for i in ["播放", "暂停", "下一首", "上一首", "停止", "搜索"]:
                if i in order_str:
                    flag_in = True
            if not flag_in:
                return

            self.ui.listWidget_2.addItem(f"{order.get('order')}")

            self.pp.say('好的主人')
            self.pp.runAndWait()

            if "播放" in order.get("order"):
                if len(order_str) > 2:
                    song_name = order_str.split("播放")[1]
                    self.ui.lineEdit.setText(song_name)
                    self.btn_search()
                    song_info = self.search_result[0]
                    self.btn_show_info(song_info)
                else:
                    self.play("play")
            elif "暂停" in order.get("order"):
                self.play("pause")
            elif "搜索" in order.get("order"):
                song = order.get("order").split("搜索")
                if len(song) > 1:
                    self.ui.lineEdit.setText(song[1])
                    self.btn_search()
            elif "下一首" in order.get("order"):
                self.play("next")
            elif "上一首" in order.get("order"):
                self.play("last")

    def handle_order(self, order):
        self.order_list.append({"order": order, "time": time.time()})

    def btn_search(self):
        text = self.ui.lineEdit.text()
        if not text:
            print("请输入搜索内容")
            return
        ret = ncm.search(text)
        self.search_result = ret
        if not ret:
            print("搜索失败")
            return
        self.ui.listWidget.clear()
        for song in ret:
            self.ui.listWidget.addItem(f'《{song.get("name")}》 - {song.get("artist")}')
        return True

    def btn_get_song(self):
        item = self.ui.listWidget.currentItem()
        if not item:
            print("请选择一首歌曲")
            return

        song_info = self.search_result[self.ui.listWidget.currentRow()]
        self.btn_show_info(song_info)

    def btn_show_info(self, song_info, play=True):

        song_id = song_info.get("id")

        pic_url = song_info.get("picUrl")
        # 将图片获取到的url转换为QPixmap
        pic_pixmap = QPixmap()
        pic_pixmap.loadFromData(requests.get(pic_url).content)
        # 将图片缩放显示到label
        self.ui.label.setPixmap(pic_pixmap.scaled(self.ui.label.width(), self.ui.label.height()))

        # 将歌曲信息显示到label_2
        self.ui.label_2.setText(f"{song_info}")

        lyric = ncm.get_song_lyrics(song_id)
        if not lyric:
            print("获取歌词失败")
            return
        self.ui.plainTextEdit.setPlainText(lyric)

        song_url = ncm.get_song(song_id)  # 获取歌曲url
        if not song_url:
            print("获取歌曲url失败")
            return

        self.ui.label_song.setText(song_info.get("name"))
        self.ui.label_time.setText(f'00:00 / {song_info.get("dT")}')
        self.current_song = song_url
        self.player.setMedia(QMediaContent(QUrl(song_url)))
        if play:
            self.flag_play = False
            self.play("play")

    def play(self, e=None):
        if not self.current_song:
            print("请选择一首歌曲")
            self.btn_show_info(self.search_result[self.song_index % len(self.search_result)])
            return
        if e == "play" and self.flag_play:
            return
        elif e == "pause" and not self.flag_play:
            return
        elif e == "next":
            self.song_index += 1
            self.btn_show_info(self.search_result[self.song_index % len(self.search_result)])
            return
        elif e == "last":
            self.song_index -= 1
            self.btn_show_info(self.search_result[self.song_index % len(self.search_result)])
            return
        else:
            pass
        if self.flag_play:
            self.player.pause()
            self.ui.pushButton_play.setText("播放")
            self.flag_play = False
        else:
            self.player.play()
            self.ui.pushButton_play.setText("暂停")
            self.flag_play = True
            # 启动定时器
            self.timer.start(1000)
        return True

    def stop(self):
        self.player.stop()
        self.ui.pushButton_play.setText("播放")
        self.flag_play = False
        self.current_song = None
        self.player.setMedia(QMediaContent(QUrl()))

    def update_time(self):
        if not self.current_song:
            return
        time = self.player.position()
        self.ui.label_time.setText(f'{ncm.ms_to_min(time)} / {ncm.ms_to_min(self.player.duration())}')

        # horizontalSlider
        self.ui.horizontalSlider.setMaximum(self.player.duration())
        self.ui.horizontalSlider.setValue(time)

        # 如果播放结束
        if time == self.player.duration():
            self.play("next")


if __name__ == '__main__':
    # 显示窗口
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
