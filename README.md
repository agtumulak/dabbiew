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
A move command can be repeated by typing the number of times to repeat before 
issuing an action. For example, to move down 12 times, simply type `12j` (or 
`12↓`). To perform a search, open the search bar with `\`, enter a substring to 
match, and hit return (`↵`).

| Key                              | Action                             |
|----------------------------------|------------------------------------|
| `v`                              | toggle selection mode              |
| `esc`                            | cancel selection                   |
| `h` `j` `k` `l` `←` `↓`  `↑` `→` | movement keys                      |
| `gg`, `GG`                       | jump to top, bottom of DataFrame   |
| `^`, `$`                         | jump to left, right of DataFrame   |
| `,`, `.`                         | decrease, increase selection width |
| `<`, `>`                         | decrease, increase all widths      |
| `t`, `y`                         | toggle header, index               |
| `/`                              | toggle search bar                  |
| `n`, `p`                         | next, previous match               |
| `d`                              | enter ipdb debug mode              |
| `q`                              | quit                               |

## Documentation
To generate the source code documentation do

```
cd doc
make html
```

and open ```_build/html/index.html```
