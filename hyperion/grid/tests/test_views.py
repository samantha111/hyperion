from copy import deepcopy

import numpy as np
import pytest

from hyperion.grid import CartesianGrid, CylindricalPolarGrid, SphericalPolarGrid, AMRGrid, OctreeGrid

ALL_GRID_TYPES = ['car', 'sph', 'cyl', 'amr', 'oct']


class TestView(object):

    def setup_method(self, method):

        # Set up grids
        self.grid = {}

        self.grid['car'] = CartesianGrid([-1., 1.], [-2., 2.], [-3., 3.])
        self.grid['cyl'] = CylindricalPolarGrid([0., 1.], [-1., 1.], [0., 2. * np.pi])
        self.grid['sph'] = SphericalPolarGrid([0., 1.], [0., np.pi], [0., 2. * np.pi])

        self.grid['amr'] = AMRGrid()
        level = self.grid['amr'].add_level()
        grid = level.add_grid()
        grid.xmin, grid.xmax = -1., 1.
        grid.ymin, grid.ymax = -1., 1.
        grid.zmin, grid.zmax = -1., 1.
        grid.nx, grid.ny, grid.nz = 8, 8, 8

        refined = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        self.grid['oct'] = OctreeGrid(0., 0., 0., 10., 10., 10., np.array(refined).astype(bool))

        # Set up empty grid class
        self.grid_empty = {}
        self.grid_empty['car'] = CartesianGrid
        self.grid_empty['cyl'] = CylindricalPolarGrid
        self.grid_empty['sph'] = SphericalPolarGrid
        self.grid_empty['amr'] = AMRGrid
        self.grid_empty['oct'] = OctreeGrid

        # Set up initial densities
        self.density = {}
        self.density['car'] = np.array([[[1.]]])
        self.density['cyl'] = np.array([[[1.]]])
        self.density['sph'] = np.array([[[1.]]])
        amr_q = deepcopy(self.grid['amr'])
        amr_q.levels[0].grids[0].quantities['density'] = np.ones((8, 8, 8))
        self.density['amr'] = amr_q['density']
        self.density['oct'] = np.ones(len(refined))

        # Set up invalid densities
        self.density_invalid = {}
        self.density_invalid['car'] = np.array([[[1., 1.]]])
        self.density_invalid['cyl'] = np.array([[[1., 1.]]])
        self.density_invalid['sph'] = np.array([[[1., 1.]]])
        amr_q = deepcopy(self.grid['amr'])
        amr_q.levels[0].grids[0].quantities['density'] = np.ones((8, 6, 8))
        self.density_invalid['amr'] = amr_q['density']
        self.density_invalid['oct'] = np.ones(len(refined) + 2)

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_get_nonexistent(self, grid_type):
        g = self.grid[grid_type]
        with pytest.raises(KeyError) as exc:
            g['density']
        assert exc.value.args[0] == "density"

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_setget_empty(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        assert g['density']
        # And the following should work, since g['density'] is a gridview
        # object, which should be viewable too
        assert g['density']['density']
        assert g['density']['density']['density']
        with pytest.raises(IndexError) as exc:
            assert g['density'][0]
        assert exc.value.args[0] == 'list index out of range'

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_single_array(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        g['density'].append(self.density[grid_type])
        assert g['density'][0]
        assert g['density'][-1]
        with pytest.raises(IndexError) as exc:
            assert g['density'][1]
        assert exc.value.args[0] == 'list index out of range'

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_single_array_invalid(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        with pytest.raises(ValueError) as exc:
            g['density'].append(self.density_invalid[grid_type])
        assert exc.value.args[0].startswith('Quantity arrays do not have the right dimensions')

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_double_array(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        g['density'].append(self.density[grid_type])
        g['density'].append(self.density[grid_type])
        assert g['density'][0]
        assert g['density'][-1]
        assert g['density'][1]
        assert g['density'][-2]
        with pytest.raises(IndexError) as exc:
            assert g['density'][3]
        assert exc.value.args[0] == 'list index out of range'

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_double_array_invalid(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        g['density'].append(self.density[grid_type])
        with pytest.raises(ValueError) as exc:
            g['density'].append(self.density_invalid[grid_type])
        assert exc.value.args[0].startswith('Quantity arrays do not have the right dimensions')

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_transfer_empty(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        h = self.grid_empty[grid_type]()
        h['density'] = g['density']

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_transfer_single(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        g['density'].append(self.density[grid_type])
        h = self.grid_empty[grid_type]()
        h['density'] = g['density']

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_recursive(self, grid_type):
        g = self.grid[grid_type]
        g['density'] = []
        with pytest.raises(Exception) as exc:
            g['density'].append(self.density[grid_type])
            g['density'].append(g['density'])
        assert exc.value.args[0] == "Calling append recursively"

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_single_view_invalid_list(self, grid_type):
        g = self.grid[grid_type]
        h = deepcopy(g)
        g['density'] = []
        h['density'] = []
        h['density'].append(self.density[grid_type])
        with pytest.raises(Exception) as exc:
            g['density'].append(h['density'])
        assert exc.value.args[0] == "Can only append a single grid"

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_append_single_view(self, grid_type):
        g = self.grid[grid_type]
        h = deepcopy(g)
        g['density'] = []
        h['density'] = []
        h['density'].append(self.density[grid_type])
        g['density'].append(h['density'][0])

    @pytest.mark.parametrize(('grid_type'), ALL_GRID_TYPES)
    def test_iadd(self, grid_type):
        g = self.grid[grid_type]
        h = deepcopy(g)
        g['density'] = []
        g['density'].append(self.density[grid_type])
        h['density'] = []
        h['density'].append(self.density[grid_type])
        g['density'][0].add(h['density'][0])
        if grid_type in ['car', 'cyl', 'sph', 'oct']:
            assert np.all(g.quantities['density'][0] == self.density[grid_type] * 2.)
        elif grid_type in ['amr']:
            assert np.all(g.levels[0].grids[0].quantities['density'] == self.density[grid_type].levels[0].grids[0].quantities['density'] * 2)