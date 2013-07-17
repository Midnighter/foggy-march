source("../analysis.R")
source("../plots.R")

my.src <- "Data"
my.out <- "Images"

# pdf(file=paste(file.path(my.out, "all"), ".pdf", sep=""),
#     title="", width=7, height=7 * 3 / 4)
# for (my.name in list.files(my.path, "*.csv")) {
#     my.df <- load_df(file.path(my.path, my.name))
#     my.plot <- plot_scaling(my.df, "Signal")
#     my.plot <- my.plot + ggtitle(sub(".csv", "", my.name))
#     print(my.plot)
# }
# dev.off()

my.buffered.files <- c("buffered_uniform_random_walk_uniform_capacity",
               "buffered_uniform_random_walk_degree_capacity",
               "buffered_varied_uniform_random_walk_uniform_capacity",
               "buffered_varied_uniform_random_walk_degree_capacity")

my.deletory.files <- c("deletory_uniform_random_walk_uniform_capacity",
               "deletory_uniform_random_walk_degree_capacity",
               "deletory_varied_uniform_random_walk_uniform_capacity",
               "deletory_varied_uniform_random_walk_degree_capacity")

my.deleted <- load_capacity(my.src, my.deletory.files)
my.buffered <- load_capacity(my.src, my.buffered.files)
