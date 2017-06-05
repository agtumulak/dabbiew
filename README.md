# DabBiew
A curses-based DataFrame viewer inspired by TabView.

## About
This is a side project for now. I work on it because I want more green squares 
on my GitHub profile.

The main difference between TabView and DabBiew is that underlying data 
structure is a pandas DataFrame instead of a list of lists. This has the 
advantage of potentially being able to take advantage of Dask, which supports 
"Big Data" collections for distributed environments.

## Usage
Open any csv file

```
dabbiew file.csv
```

## Key Bindings
| Key        | Action                   |
|------------|--------------------------|
| `q`        | quit                     |
| `v`        | toggle selection mode    |
| `esc`      | cancel selection         |
| `l` or `→` | move right               |
| `j` or `↓` | select down              |
| `h` or `←` | select left              |
| `k` or `↑` | select up                |
| `.`        | increase selection width |
| `,`        | decrease selection width |
| `t`        | toggle header            |
| `y`        | toggle index             |

## Documentation
To generate the source code documentation do

```
cd doc
make html
```

and open ```_build/html/index.html```
