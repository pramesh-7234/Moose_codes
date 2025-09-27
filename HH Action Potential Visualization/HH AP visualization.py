import moose
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import plotly.express as px
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import plotly.graph_objects as go
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QGridLayout,QHBoxLayout,QDoubleSpinBox,QLabel,QSlider
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# creating the containers, compartments and channels

container=moose.Neutral('/sim')
model=moose.Neutral(f'{container.path}/model')
data=moose.Neutral(f'{container.path}/data')
axon=moose.Compartment(f'{model.path}/axon')

kchan=moose.HHChannel(f'{axon.path}/K')
moose.connect(kchan,'channel',axon,'channel')

# setting the parameters:

axon.Em=0
axon.initVm=0
axon.Cm=1
axon.Rm=1/0.3

# Setting up the K channel

kchan.Ek=-12
kchan.Gbar=36
kchan.Xpower=4

n_gate=moose.HHGate(f'{kchan.path}/gateX')
n_alpha_params=[0.1, -0.01, -1.0, -10.0, -10.0]
n_beta_params=[0.125, 0, 0, 0, 80.0]

vdivs=150
vmin=-30
vmax=120

n_params=n_alpha_params+n_beta_params+[vdivs,vmin,vmax]
n_gate.setupAlpha(n_params)

# Setting up the Na channel

nachan=moose.HHChannel(f'{axon.path}/Na')
moose.connect(nachan,'channel',axon,'channel')

nachan.Ek=115
nachan.Gbar=120
nachan.Xpower=3
nachan.Ypower=1

# HH type gates and parameters

m_gate=moose.HHGate(f'{nachan.path}/gateX')
h_gate=moose.HHGate(f'{nachan.path}/gateY')

m_alpha_params=[2.5, -0.1, -1.0, -25.0, -10.0]
m_beta_params=[4, 0, 0, 0, 18.0]

h_alpha_params=[0.07, 0, 0, 0, 20.0]
h_beta_params=[1, 0, 1, -30, -10.0]


m_params=m_alpha_params+m_beta_params+[vdivs,vmin,vmax]
h_params=h_alpha_params+h_beta_params+[vdivs,vmin,vmax]
m_gate.setupAlpha(m_params)
h_gate.setupAlpha(h_params)

# Creating a Pulse Generator

pulse=moose.PulseGen(f'{model.path}/pulse')
moose.connect(pulse,'output',axon,'injectMsg')
pulse.baseLevel=0
pulse.width[0]=90
pulse.delay[0]=10

# setting up tables for recording

gK_tab=moose.Table(f'{data.path}/K')
gNa_tab=moose.Table(f'{data.path}/Na')
Vm_tab=moose.Table(f'{data.path}/Vm')
moose.connect(gK_tab,'requestOut',kchan,'getGk')
moose.connect(gNa_tab,'requestOut',nachan,'getGk')
moose.connect(Vm_tab,'requestOut',axon,'getVm')

n_tab=moose.Table(f'{data.path}/n_particle')
moose.connect(n_tab,'requestOut',kchan,'getX')
m_tab=moose.Table(f'{data.path}/m_particle')
moose.connect(m_tab,'requestOut',nachan,'getX')
h_tab=moose.Table(f'{data.path}/h_particle')
moose.connect(h_tab,'requestOut',nachan,'getY')

def run_simulation(I_inj):
    pulse.level[0]=I_inj
    simtime=110
    moose.reinit()
    moose.start(simtime)

    globals()['t']=np.arange(len(Vm_tab.vector))*Vm_tab.dt





class PlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Squid Giant Axon HHM Moose model")
        self.setGeometry(500, 200, 800, 800)

        # Main vertical layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("Injected Current: 10 µA/cm²")
        self.current_slider=QSlider(Qt.Horizontal)
        self.current_slider.setRange(0, 100)
        self.current_slider.setValue(10)
        self.current_slider.setTickInterval(1)
        self.current_slider.valueChanged.connect(self.update_slider_label)
        

        slider_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.current_slider)
        main_layout.addLayout(slider_layout)

        # Plot area (canvas)
        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.ax = self.canvas.figure.add_subplot(111)
        main_layout.addWidget(self.canvas)

        # Grid layout for buttons
        grid = QGridLayout()
        main_layout.addLayout(grid)

        # Define buttons and connect to their functions
        buttons = [
            ("Membrane Potential", self.plot_Vm),
            ("Sodium Conductance", self.plot_Na_cond),
            ("Potassium Conductance", self.plot_K_cond),
            ("n gating particle", self.plot_n),
            ("m gating particle", self.plot_m),
            ("h gating particle", self.plot_h)
        ]

        # Add buttons to grid (3 rows x 2 columns)
        for index, (label, function) in enumerate(buttons):
            row = index // 2
            col = index % 2
            btn = QPushButton(label)
            btn.clicked.connect(function)
            grid.addWidget(btn, row, col)

    def update_slider_label(self):
        value=self.current_slider.value()
        self.slider_label.setText(f'Injected Current: {value:.1f} µA/cm²')


    def clear_plot(self):
        self.ax.clear()

    def plot_Vm(self):
        self.clear_plot()

        I_inj = self.current_slider.value()
        run_simulation(I_inj)            
    
        x = t
        self.ax.plot(x, Vm_tab.vector, label='Vm')
        self.ax.set_title("Membrane Potential")
        self.ax.set_ylabel('Potential (mv)')
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

    def plot_Na_cond(self):
        self.clear_plot()

        I_inj = self.current_slider.value() 
        run_simulation(I_inj)      
        
        x = t
        self.ax.plot(x, gNa_tab.vector, label='gNa')
        self.ax.set_title("Sodium conductance")
        self.ax.set_ylabel('Conductance (mS/cm^2)')
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

    def plot_K_cond(self):
        self.clear_plot()

        I_inj = self.current_slider.value() 
        run_simulation(I_inj)      
        
        x = t
        self.ax.plot(x, gK_tab.vector,label='gK')
        self.ax.set_title("Potassium conductance")
        self.ax.set_ylabel('Conductance (mS/cm^2)')
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

    def plot_n(self):
        self.clear_plot()

        I_inj = self.current_slider.value() 
        run_simulation(I_inj)      
        
        x = t
        self.ax.plot(x, n_tab.vector, label='n(fraction open)')
        self.ax.set_title("n gating particle (K channel)")
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

    def plot_m(self):
        self.clear_plot()

        I_inj = self.current_slider.value() 
        run_simulation(I_inj)      
        
        x = t
        self.ax.plot(x, m_tab.vector, label='m(fraction open)')
        self.ax.set_title("m gating particle (Na channel)")
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

    def plot_h(self):
        self.clear_plot()

        I_inj = self.current_slider.value() 
        run_simulation(I_inj)      
        
        x = t
        self.ax.plot(x, h_tab.vector, label='h(fraction open)')
        self.ax.set_title("h gating particle (Na channel)")
        self.ax.set_xlabel('Time (ms)')
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
