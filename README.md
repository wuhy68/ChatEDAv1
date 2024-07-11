# ChatEDAv1
ChatEDA: A Large Language Model Powered Autonomous Agent for EDA

## Overview
The integration of a complex set of Electronic Design Automation (EDA) tools to enhance interoperability is a critical concern for circuit designers.
Recent advancements in large language models (LLMs) have showcased their exceptional capabilities in natural language processing and comprehension, offering a novel approach to interfacing with EDA tools. 
This research paper introduces ChatEDA, an autonomous agent for EDA empowered by a large language model, AutoMage, complemented by EDA tools serving as executors.
ChatEDA streamlines the design flow from the Register-Transfer Level (RTL) to the Graphic Data System Version II (GDSII) by effectively managing task planning, script generation, and task execution.
Through comprehensive experimental evaluations, ChatEDA has demonstrated its proficiency in handling diverse requirements, and our fine-tuned AutoMage model has exhibited superior performance compared to GPT-4 and other similar LLMs.

## EDA Tool Instruction Dataset
We propose some examples of [EDA tool instructions datasets](https://github.com/wuhy68/ChatEDAv1/blob/master/data/train/ChatEDA-train-example.json) for the training of AutoMage models, the controller of ChatEDA.

## ChatEDA-Bench
[ChatEDA-Bench](https://github.com/wuhy68/ChatEDAv1/blob/master/data/test/ChatEDA-Bench.txt) is a comprehensive evaluation benchmark comprising 50 distinct tasks to evaluate the performance of LLMs in automating the EDA flow.

## API Document
To facilitate better understanding of Python-EDA interface document, we provide the [API document](https://github.com/wuhy68/ChatEDAv1/blob/master/api_doc/openroad_api.py) and the corresponding [OpenRoad implementation](https://github.com/wuhy68/ChatEDAv1/blob/master/api_doc/openroad_api_impl.py).

## Citation
```bibtex
@article{wu2024chateda,
  title={ChatEDA: A Large Language Model Powered Autonomous Agent for EDA},
  author={Wu, Haoyuan and He, Zhuolun and Zhang, Xinyun and Yao, Xufeng and Zheng, Su and Zheng, Haisheng and Yu, Bei},
  journal={IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  year={2024},
  publisher={IEEE}
}
```

## License
This repo is licensed under the [Apache 2.0 License](https://github.com/wuhy68/ChatEDAv1/blob/master/LICENSE). 
