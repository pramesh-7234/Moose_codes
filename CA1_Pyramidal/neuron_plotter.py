from vedo import Plotter, Lines, Points
import numpy as np

def load_swc(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = list(map(float, line.strip().split()))
            data.append(parts)
    return np.array(data)

def plot_neuron_3d(data):
    segments_apical = []
    segments_basal = []
    segments_other = []
    soma_coords = []

    for point in data:
        n, t, x, y, z, r, parent = point
        if parent == -1:
            continue
        parent_point = data[int(parent) - 1]
        x2, y2, z2 = parent_point[2:5]
        t_parent = parent_point[1]

        seg = [[x, y, z], [x2, y2, z2]]
        if t == 4 or t_parent == 4:
            segments_apical.append(seg)
        elif t == 3 or t_parent == 3:
            segments_basal.append(seg)
        else:
            segments_other.append(seg)

    soma_points = data[data[:, 1] == 1][:, 2:5]

    lines_apical = Lines(segments_apical, c='orange', lw=1)
    lines_basal = Lines(segments_basal, c='blue', lw=1)
    lines_other = Lines(segments_other, c='gray', lw=1)
    soma = Points(soma_points, r=12, c='black')



    plt = Plotter(title='GPU Neuron Morphology', axes=1, bg='white')
    plt.show(lines_apical, lines_basal, lines_other, soma, interactive=True)
if __name__=='__main__':
    # Path to SWC file
    file_path = '/home/pramesh/MOOSE_STUFF/CA1_Pyramidal/052714C_37.swc'
    swc_data = load_swc(file_path)
    plot_neuron_3d(swc_data)
