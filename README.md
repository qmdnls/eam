# eam

A tool for automated Enterprise Architecture modeling in Archimate written as part of my thesis project.

eam implements a HMM which models the current network state using evidence that has been collected from network traffic on different clients. These clients send the network traffic which updates the HMM periodically. The network state is stored in a Neo4j graph database. Using `retrieve.py` you can output an XML file with the current estimated network state that is stored in the graph database. This file can easily be converted to an Archimate model by mapping its XML schema to the Archimate XML schema.

This tool is still WIP.

**Abstract** Enterprise Architecture modeling is an approach to manage modern IT infrastructure and lansdcapes to coordinate a multitude of IT projects in an organization using modeling tools such as Archimate. Because these models have traditionally been created and maintained manually, efforts to manage IT architecture have been both time-consuming and error-prone. We will evaluate an approach suggested by Johnson et al. (2016) for automated generation of these models from observed network traffic using Dynamic Bayesian Networks. As inference in this very large Dynamic Bayesian Network proves intractable we will propose an alternative approach using a set of many Hidden Markov Models to model the network state, present an implementation and evaluate its performance in a real-world setting.
 
## Dependencies

Python 3
Neo4j

## Installation

Clone the repository and run `pip install -r requirements.txt` (or use a venv) to install the required Python packages.

## Usage

Run `client.py` on clients where evidence should be collected, run `server.py` on the same machine as the Neo4j database. Use `retrieve.py` to output the current estimated network state.
