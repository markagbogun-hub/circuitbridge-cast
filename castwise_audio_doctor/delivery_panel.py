try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QLabel, QFormLayout, QDoubleSpinBox
except Exception:
    QWidget = object

from .delivery_profiles import profile_names, get_profile

class DeliveryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = get_profile("Radio")
        if QWidget is object:
            return
        layout = QVBoxLayout(self)
        self.selector = QComboBox()
        self.selector.addItems(profile_names())
        self.status = QLabel("Delivery Check: not run")
        self.run_button = QPushButton("Run Delivery Check")
        layout.addWidget(QLabel("Delivery Profile"))
        layout.addWidget(self.selector)
        layout.addWidget(self.status)
        layout.addWidget(self.run_button)
        self.selector.currentTextChanged.connect(self._changed)

    def _changed(self, name):
        self.profile = get_profile(name)
        self.status.setText(f"Profile: {name}")

    def set_result(self, result):
        self.status.setText(f"Delivery Check: {result.status}")
