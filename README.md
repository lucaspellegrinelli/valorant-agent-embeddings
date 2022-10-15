# VALORANT Agent Embeddings

The goal of this project is create contextual embeddings for VALORANT agents with respect to the composition it is inserted into. For example, a Viper with a second controller played on Bind may have a very different play style / role from a Viper played on the same map but without a second controller.

## How it works?

### Model training

The idea for training the neural network is making it learn to fill a 4 player composition with what's missing. We generate the dataset by having a lot of compositions gathered from professional matchs and then removing one of the agents in there to have our 4 player input. The goal for the neural network will be predicting what was that 5th player we removed, so that's our label for the supervised training.

<p align="center">
  <img width="75%" src="https://i.imgur.com/pfigRqI.png">
</p>

### Model architecture

I used a multi input and multi output autoencoder for this task. The idea is having the inputs being the agent for each of the four players (one hot encoded since it's categorical), the map (also one hot encoded) and the stats for each of the four player. That leaves us with 3 input for the neural network:
 - Agent Input shape: `(4, number_of_agents_in_the_game)`
 - Map Input shape: `(number_of_maps_in_the_game)`
 - Stats Input shape: `(4, number_of_stats_for_each_player)`

For the output, we only want one agent and we don't need to predict the map the composition was played, so that leaves us with 2 outputs:
 - Agent Input shape: `(number_of_agents_in_the_game)`
 - Stats Input shape: `(number_of_stats_for_each_player)`
 
In the middle of the neural network there's the latent dimension. It is very important in autoencoder since it forces the neural network to learn a compact representation of the data it needs - in this case the agent we want to predict. That will be our embedding.

The exact values for the number of layers, number of neurons and etc are optimized, so I won't be specifying those here.

<p align="center">
  <img width="100%" src="https://i.imgur.com/j7vOo2x.png">
</p>

### Data Scraping

Data was scraped from the website vlr.gg and includes the agents each player played on each map and some of their statistics (like Average Combat Score, Average Damager per Round, First Kills, First Deaths, KAST ...).

<p align="center">
  <img width="100%" src="https://i.imgur.com/EbkmB50.png">
</p>


