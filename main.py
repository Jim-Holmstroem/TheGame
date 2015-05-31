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


class KeyInputStateMachine(object):  # receives all keydown events
    def render(self, game):
        pass


@curry
def handle_event(game, event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            pygame.quit()
            sys.exit()
        if event.key in directions.keys():
            game.focused_node = game.focused_node.children[event.key] if event.key in game.focused_node.children \
                else game.focused_node.node(game, event.key)
        if event.key == pygame.K_b:
            game.focused_node = game.focused_node.parent
        if event.key == pygame.K_w:
            children = game.focused_node.children
            game.focused_node = children.values()[0] if len(children) == 1 else game.focused_node


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
    def __init__(self, position, r=32, energy=0, health=128, children=None, parent=None):
        self.position = position
        self.r = r
        self.energy = energy
        self.max_energy = (4 * r/128)**2
        self.health = health
        self.max_health = 128
        self.children = children if children is not None else {}
        self.parent = parent if parent is not None else self

    def update(self, game):
        self.energy = min(self.energy+0.01, self.max_energy) if self is game.mother_node else self.energy
        def energy_flow(child, n_children=len(self.children)):
            old_energy = child.energy
            potential_flow = (self.energy-child.energy)/(16 * n_children)
            child.energy += potential_flow
            child.energy = min(child.energy, child.max_energy)
            child.energy = max(child.energy, 0)
            actual_flow = child.energy - old_energy
            return actual_flow


        self.energy -= sum(map(energy_flow, self.children.values()))

        list(map(methodcaller('update', game), self.children.values()))

    def collides(self, position, r):
        """
        node with position and radius r
        collides with the subtree of self
        """
        slack = 0.99
        squared_distance = (
            (self.position[0]-position[0])**2 +
            (self.position[1]-position[1])**2
        )

        return (squared_distance < slack * (r+self.r)**2) or any(
            map(
                methodcaller('collides', position, r),
                self.children.values()
            )
        )

    def render(self, game):
        @curry
        def render_circle(color, width, r):
            pygame.draw.circle(
                game.surface,
                color,
                tuple(map(int, self.position)),
                int(r),
                int(width),
            )

        render_circle(
            base_color,
            0,
            self.r * sqrt(self.energy/self.max_energy)
        )
        list(map(
            render_circle((220, 10, 15), 1),
            map(lambda i: self.r*sqrt(i/4), range(1, 4+1))
        ))

        render_circle(
            (220, 10, 15) if self is not game.focused_node else focused_color,
            4 * (self.health/self.max_health),
            self.r
        )

        def render_connection(item):
            key, node = item
            tangent = p_between(self.position, node.position)
            #width=0.5
            #pygame.draw.line(
            #    game.surface,
            #    (150, 210, 60),
            #    p_between(self.position, tangent),
            #    p_between(node.position, tangent),
            #    4
            #)
            #game.surface.blit(
            #    base_font.render(key.name(), True, (255, 255, 255)),
            #    p_between(tangent, node.position)
            #)


        list(map(
            juxt([
                compose(methodcaller('render', game), itemgetter(1)),
                render_connection,
            ]),
            self.children.items()
        ))


    def node(self, game, key):
        r = 32
        w = 2 * pi * directions[key]/8
        position = (
            self.position[0]+(self.r+r)*cos(w),
            self.position[1]+(self.r+r)*sin(w),
        )
        if not game.mother_node.collides(position, r) and self.energy >= self.max_energy/4:
            self.energy -= self.max_energy/4
            node = Node(
                position,
                r=r,
                parent=self,
            )

            self.children.update({key: node})

            return node

        else:
            return self

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
                            self.children.values()  # TODO proper printing of dictionary
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
        mother_node=Node(
            (512, 512),
            r=64,
        ),
    )

    while True:
        list(map(handle_event(game), pygame.event.get()))
        game.mother_node.update(game)
        surface.fill(pygame.Color('black'))
        game.mother_node.render(game)

        pygame.display.flip()

        time_elapsed = clock.tick(30)
