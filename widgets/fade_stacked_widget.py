from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

class FadeStackedWidget(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.duration = 500
        self.easing_curve = QEasingCurve.Type.InOutQuad # Kiểu chuyển động mượt

    def fade_to_widget(self, widget):
        if self.currentWidget() == widget:
            return

        #Chuẩn bị widget mới (Set độ trong suốt = 0 để ẩn nó đi)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0)
        
        #Chuyển stack sang widget mới ngay lập tức
        self.setCurrentWidget(widget)
        
        #Tạo Animation: Tăng độ rõ từ 0 lên 1
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(self.duration)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(self.easing_curve)
        
        self.anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        
        self.anim.start()