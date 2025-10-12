
import streamlit as st
import pandas as pd
import random

# this module assigns species to newly created persons based on the year of their birth +/- CE.

class Species:

    def __init__(self, yearsbp):
        self.yearsbp = yearsbp
        self.species = self.get_species()

    def get_species(self):
        # get list of species available in the year bp

        # assign species to person based on year of bir
        return species_list

    def species_assigner(year):
        if year <= -35000:
            species_list= ['sapiens', 'neanderthalensis', 'denisovan', 'floresiensis'])
            species = random.choices(species_list, cum_weights=[70,90, 95, 100], k=1)
        elif year <= -10000:
            species_list= ['sapiens', 'neanderthalensis', 'denisovan', 'floresiensis']
            species = random.choices(species_list, cum_weights=[97, 98, 99, 100], k=1)
        elif year <= 2150:
            species_list= ['sapiens']
            species = random.choices(species_list, cum_weights=[100], k=1)

        elif year <= 3500:
            species_list= ['sapiens', 'AI', 'cyborg', 'GMO', 'novel']
            species = random.choices(species_list, cum_weights=[90, 93, 95,98, 100], k=1)
        
        elif year <= 100000:
            species_list= ['sapiens', 'AI', 'cyborg', 'GMO', 'novel']
            species = random.choices(species_list, cum_weights=[90, 93, 95,98, 100], k=1)
        
        else:
            species_list= ['sapiens', 'AI', 'cyborg', 'GMO', 'novel']
            species = random.choices(species_list, cum_weights=[90, 93, 95,98, 100], k=1)
        return species

