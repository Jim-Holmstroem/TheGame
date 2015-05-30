from __future__ import print_function, division

from operator import *
from math import (
    cos,
    sin,
    tan,
    pi,
    sqrt,
)
import sys
from time import sleep

from toolz.curried import *

import pygame
pygame.init()
sys.setrecursionlimit(1024*64)
W, H = 1366, 768

directions = {
    pygame.K_a: 2,
    pygame.K_s: 3,
    pygame.K_d: 4,
    pygame.K_f: 5,
    pygame.K_j: 6,
    pygame.K_k: 7,
    pygame.K_l: 0,
    pygame.K_SEMICOLON: 1,
}

@curry
def handle_event(game, event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            pygame.quit()
            sys.exit()
        if event.key in directions.keys():
            game.focused_node = game.focused_node.node(game.focused_node.r, directions[event.key])
        if event.key == pygame.K_b:
            parent = game.focused_node.parent
            game.focused_node = parent if parent is not None else game.focused_node


tab = map("    {}".format)

def p_between(p_a, p_b):
    return (
        (p_a[0]+p_b[0])/2,
        (p_a[1]+p_b[1])/2,
    )

p_add = compose(list, map(add))
p_sub = compose(list, map(sub))


base_color = (60, 150, 210)
focused_color = (200, 200, 0)
base_font = pygame.font.SysFont('monospace', 20)


class Node(object):
    def __init__(self, position, r=32, energy=4, children=(), parent=None):
        self.position = position
        self.r = r
        self.energy = energy
        self.max_energy = 128
        self.children = children
        self.parent = parent

    def update(self, game):
        self.energy = min(self.energy+1, self.max_energy)
        list(map(methodcaller('update', game), self.children))

    def render(self, game):
        pygame.draw.circle(
            game.surface,
            base_color,
            tuple(map(int, self.position)),
            int(self.r*sqrt(self.energy/self.max_energy)),
            0
        )
        pygame.draw.circle(
            game.surface,
            base_color if self is not game.focused_node else focused_color,
            tuple(map(int, self.position)),
            int(self.r),
            2
        )
        def render_connection(node):
            tangent = p_between(self.position, node.position)
            width=0.5
            pygame.draw.line(
                game.surface,
                (150, 210, 60),
                p_between(self.position, tangent),
                p_between(node.position, tangent),
                4
            )

        list(map(
            juxt([
                methodcaller('render', game),
                render_connection,
            ]),
            self.children
        ))

    def node(self, r, direction):
        w = 2*pi*direction/8
        node = Node(
            (
                self.position[0]+(self.r+r)*cos(w),
                self.position[1]+(self.r+r)*sin(w),
            ),
            parent=self,
        )
        self.children = self.children + (node, )

        return node

    def __str__(self):
        return "Node(\n    position={},\n    r={},\n    self.children=[\n{}    ],\n)\n".format(
            self.position,
            self.r,
            "\n".join(
                tab(
                    concat(
                        map(
                            compose(
                                methodcaller('split', '\n'),
                                str
                            ),
                            self.children
                        )
                    )
                )
            )
        )


class Game(object):
    def __init__(self, surface, mother_node, focused_node=None):
        self.surface = surface
        self.mother_node = mother_node
        self.focused_node = focused_node if focused_node is not None else mother_node


if __name__ == "__main__":

    surface = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    game = Game(
        surface=surface,
        mother_node=Node((512, 512)),
    )

    while True:
        list(map(handle_event(game), pygame.event.get()))
        game.mother_node.update(game)
        surface.fill(pygame.Color('black'))
        game.mother_node.render(game)

        pygame.display.flip()

        time_elapsed = clock.tick(30)
