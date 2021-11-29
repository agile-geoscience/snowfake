# -*- coding:utf-8 -*-
"""
Make Gravner-Griffeath snowfakes.

Implementing:
Janko Gravner, David Griffeath,
Modeling snow crystal growth II: A mesoscopic lattice map with plausible dynamics,
Physica D: Nonlinear Phenomena, Volume 237, Issue 3, 2008, Pages 385-404,
https://doi.org/10.1016/j.physd.2007.09.008.

Author: Matt Hall
Email: matt@agilescientific.com
Licence: Apache 2.0
"""
import numpy as np
import scipy.signal as ss
from tqdm import tqdm
from scipy.signal import convolve2d
from scipy.ndimage import affine_transform
import matplotlib.pyplot as plt
from functools import partial


class Snowfake:
    """
    Simulates a snowfake (fake snowflake), with a slow implementation
    of Gravner & Griffeath's algorithm. This class holds all of the state,
    so you can grow it in stages, eg changing some of the parameters
    at various times.

    Example parameters:

    # Figure 9b.
    params =  {
        'ρ': 0.41,
        'β': 1.3,
        'α': 0.08,
        'θ': 0.025,
        'κ': 0.003,
        'μ': 0.07,
        'γ': 0.00005,
        'σ': 0.0,
    }
    """

    NBR = np.array([[0, 1, 1],
                    [1, 1, 1],
                    [1, 1, 0]])

    BDY = np.array([[0,  1, 1],
                    [1, -7, 1],
                    [1,  1, 0]])

    def __init__(self, size, random=False, **kwargs):
        """
        a(t): attachment at time t
        b(t): boundary mass (quasi-liquid)
        c(t): crystal mass (ice)
        d(t): diffusive mass (vapour)
        
        Recall that ξ t (x) = (a t (x), b t (x), c t (x), d t (x)), with
        a_0(0) = c_0(0) = 1,
        b_0(0) = d_0(0) = 0; and for all x != 0,
        a_0(x) = b_0(x) = c_0(x) = 0, and d_0(x) = ρ.
        
        This initialization corresponds to a mesoscopic prism at the origin
        surrounded by homogeneous vapor with density ρ (which could be a matrix).
        """
        self.__dict__.update(**kwargs)
        self.a = centre(size, fill=0, centre=1)
        self.b = centre(size, fill=0, centre=0)
        self.c = centre(size, fill=0, centre=1)
        self.d = centre(size, fill=self.ρ, centre=0)
        self._random = random
        if self._random:
            self._rng = np.random.default_rng(self._random)
        else:
            self._rng = None
        self._size = size
        self._epochs = 0
        self._boundary_changed = True
        return

    def __repr__(self):
        return f"Snowfake(size={self._size}, epochs={self._epochs})"
    
    @property
    def neighbours(self):
        if self._boundary_changed:
            n = ss.convolve2d(self.a, self.BDY, mode='same')
            self._neighbours = n
        return np.clip(self._neighbours, 0, 6)

    @property
    def boundary(self):
        if self._boundary_changed:
            self._boundary = self.neighbours > 0
            self._boundary_changed = False
        return self._boundary    

    def diffusion(self):
        """
        "Diffusive mass evolves on A^c_t (non-crystal) by discrete diffusion with
        uniform weight 1/7 on the center site and each of its neighbors [...]
        and for x ∈ ∂A_t (boundary) any term in the sum corresponding to y ∈ A_t is
        replaced by d°(x) [i.e. the value before step]."
        """
        d_ = ss.convolve2d(self.d, self.NBR / 7, boundary='symm', mode='same')  # Eq 1.
        d_ *= 1 - self.a  # To eliminate crystal.
        self.d = d_ + self.neighbours * self.d / 7
        return
        
    def freezing(self):
        """
        "Proportion κ of the diffusive mass at each boundary site crystallizes.
        The remainder (proportion 1 − κ) becomes boundary mass."
        We control the 'boundaryness' with the boundary array.
        """
        self.b += self.boundary * (1 - self.κ) * self.d  # Eq 2a.
        self.c += self.boundary * self.κ * self.d        # Eq 2b.
        self.d -= self.boundary * self.d                 # Eq 2c.
        return
    
    def attachment(self):
        """
        "This key step in the algorithm decides when a boundary site joins the snowflake."
        What happens depends on how many neighbours a site has.
        """
        # Eq 3a: 1 or 2 neighbours.
        self.a += ((self.neighbours == 1) + (self.neighbours == 2)) * (self.b >= self.β)

        # Eq 3b: 3 neighbours. Involves dmc = diffusive_mass_criterion.
        dmc = (convolve2d(self.d, self.NBR, boundary='symm', mode='same') < self.θ) & (self.b >= self.α)
        self.a += (self.neighbours == 3) * ((self.b >= 1) | dmc)
        
        # Eq 3c: 4+ neighbours
        self.a += (self.neighbours >= 4)
        
        # Eq 3d: If a site is attached, b turns completely into c.
        diff = self.boundary * self.a * self.b
        self.c += diff
        self.b -= diff

        # Trigger update to boundary.
        self._boundary_changed = True
        return
    
    def melting(self):
        """
        "Proportion µ of the boundary mass and proportion γ of the crystal mass
        at each boundary site become diffusive mass. [...] Typically µ is small
        and γ extremely small."
        """
        # Eq 4. Change d before b and c change.
        self.d += self.boundary * (self.μ * self.b + self.γ * self.c)
        self.b -= self.boundary * self.μ * self.b
        self.c -= self.boundary * self.γ * self.c
    
    def perturb(self):
        """
        "The diffusive mass at each site undergoes a [...] perturbation of
        proportion σ"
        
        In the paper, both random and biased perturbations are used.
        """
        if self._random:
            f = partial(self._rng.choice, a=[-1, 1])
        else:
            f = lambda size: np.ones(size)
        self.d *= 1 + self.σ[self._epochs] * f(size=self.a.shape)  # Eq 5.
        return
    
    def rectify_skimage(self, prop='c'):
        """Transform to Cartesian coordinates with skimage."""
        from skimage import transform
        img = transform.rotate(getattr(self, prop), 45.0, resize=True, mode='edge')
        heximg = transform.rescale(img, (1/np.sqrt(3), 1))
        h, w = np.array(heximg.shape) // 2
        return heximg[:, w-h:w+h]
    
    def rectify(self, prop='c'):
        """Transform to Cartesian coordinates with scipy."""
        # Translation.
        origin = np.array([[1, 0, self._size/2],
                           [0, 1, self._size/2],
                           [0, 0,            1]])

        # Rotate by 45 deg.
        rotate = np.array([[ np.cos(np.pi/4), -np.sin(np.pi/4), 0],
                           [ np.sin(np.pi/4),  np.cos(np.pi/4), 0],
                           [               0,                0, 1]])

        # Squash by 1/sqrt(3)
        scale = np.array([[ 1/np.sqrt(3), 0, 0],
                          [            0, 1, 0],
                          [            0, 0, 1]])

        revert = np.array([[1, 0, -self._size/2],
                           [0, 1, -self._size/2],
                           [0, 0,             1]])

        M = origin @ rotate @ scale @ revert
        return affine_transform(getattr(self, prop), M, mode='nearest')
    
    def plot(self, ax=None, clip=0.025, d_cmap='Blues', c_cmap='Blues', d_alpha=0.25):
        """
        Not sure what the prettiest way to plot these things is.
        For now we'll do something very simple, which looks a little
        bit like what the authors do in their paper:
        Plot the sum of the d and c arrays.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
        c = self.rectify('c')
        d = 1.5 * self.rectify('d')
        ax.imshow(c+d, cmap="Blues")
        ax.axis('off')
        return ax
        
    def snapshot(self):
        """Quick look at the arrays during training."""
        props = {'a': 'attachment', 'b': 'quasi-liquid', 'c': 'ice', 'd': 'diffusion'}
        fig, axs = plt.subplots(ncols=4, figsize=(16, 4))
        for ax, prop in zip(axs, 'abcd'):
            ax.imshow(self.rectify(prop), origin='lower', interpolation='none')
            ax.set_title(props.get(prop))
            ax.axis('off')
        plt.show()
        return
        
    def grow(self, max_epochs=20_000, early_stopping=True, snapshot=True):
        if isinstance(self.σ, float):
            self.σ = self.σ * np.ones(max_epochs)
        pbar = tqdm(range(max_epochs))
        for epoch in pbar:

            # The algorithm:
            _ = self.diffusion()
            _ = self.freezing()
            _ = self.attachment()
            _ = self.melting()
            if self.σ[epoch]:
                _ = self.perturb()  # Noise or bias.

            # Some conveniences:
            pbar.set_description(f'{int(self.a.sum()):7d} attachments')
            if (epoch > 0) and early_stopping and (epoch % 100 == 0):
                if sum(self.c[self._size//2] > 0) > 0.5 * self._size:
                    break
            if (epoch > 0) and snapshot and (epoch % 1000 == 0):
                self.snapshot()
            self._epochs += 1
        return


def centre(size, fill=0, centre=1):
    """
    Make an array full of something, with something else at the centre.
    """
    arr = np.ones((size, size)) * fill
    c = int(size // 2)
    arr[c, c] = centre
    return arr


def main():
    pass


if __name__ == "__main__":
    main()
