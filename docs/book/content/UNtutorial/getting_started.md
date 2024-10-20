---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(Chap_UNtutor_getstart)=
# Getting Started

(Sec_UNtutor_schedule)=
## Schedule
For the October 21-25, 2024 United Nations `OG-PHL` training in Manila, we will be following the schedule in {numref}`table-schedule`.

```{list-table} UN OG-PHL 5-day training schedule
:header-rows: 1
:name: table-schedule

* - Day
  - Session
  - Topic
* - Mon.
  - Morning
  - Organizer introductions <br> Setup Python, Git, GitHub, and OG-PHL
* -
  - Afternoon
  - Theory: "Simple" 3-period-lived agent model
* - Tue.
  - Morning
  - Review 3-period-lived-agent exercises <br> Review OG-Core and OG-PHL modules <br> Quick Git and GitHub workflow review
* -
  - Afternoon
  - Running OG-PHL, inputs, outputs <br> Calibrating OG-PHL, current state, still to do
* - Wed.
  - Morning
  - Running OG-PHL: Revisit some reforms from 2-day visit <br> Talk about new reforms, create project teams
* -
  - Afternoon
  - OG-PHL output: Tools to visualize/tabulate output <br> OG-PHL built-in calibration helps
* - Thu.
  - Morning
  - Calibrating OG-PHL: Issues and hot spots
* -
  - Afternoon
  - Calibrating OG-PHL: Issues and hot spots
* - Fri.
  - Morning
  - Open work, project hackathon, office hours <br> Advanced topics: Adding trade, connecting to other models
* -
  - Afternoon
  - Presentation of projects <br> Future work, research, collaboration, final topics <br> Closing remarks
```

(Sec_UNtutor_python)=
## Install Python
`OG-PHL` is a large-scale overlapping generations macroeconomic model of Philippine fiscal policy. It is written in the [Python](https://www.python.org/) programming language. You will need to have some distribution of Python loaded on your computer to run the code. We recommend installing the [Anaconda](https://www.anaconda.com/download) distribution of Python. This is the most widely used Python distribution. And it has package management features, like conda environments, that we will make use of.

### Verifying you have already installed Python and Conda
If you have already installed the Anaconda distribution of Python, do the following steps to verify your installation.

#### For Windows and Mac
If you are using computer with a Windows operating system, open your Anaconda prompt. If you are using a Mac operating system, open your terminal.
- To see if you have Python installed, type `python --version`. This command should result in output like `Python 3.9.17`.
```{code}
>>> python --version
Python 3.9.17
```
- To see if you have Anaconda's conda package installed type `conda --version`. This command should results in output like `conda 23.9.0`.
```{code}
>>> conda --version
conda 23.9.0
```

#### For Linux
If you are using a computer with a Linux operating system, open your terminal.
- To see if you have Python installed, type `python -version`. This command should result in output like `Python 3.9.17`.
```{code}
>>> python -version
Python 3.9.17
```
- To see if you have Anaconda's conda package installed type `conda -version`. This command should results in output like `conda 23.9.0`.
```{code}
>>> conda -version
conda 23.9.0
```

### Installing Anaconda distribution of Python
To install the Anaconda distribution of Python, go to https://www.anaconda.com/download and select "Skip registration" to avoid giving your email address.


## Installing Git and GitHub

### Verifying you have already installed Git

### Set up a GitHub account

### Fork and clone OG-PHL repository

## Creating the ogphl-dev conda environment

## Using Jupyter notebooks
A nice way to execute lines of code on your local computer is to use Jupyter notebooks
