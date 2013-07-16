source("../analysis.R")
source("../plots.R")

my.path <- "Data"
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

load_capacity <- function(my.files)
{
    my.res <- data.frame()
    for (my.name in my.files) {
        my.df <- load_df(file.path(my.path, paste(my.name, ".csv", sep="")))
        # drop type variable
        my.df <- with(my.df, my.df[type == "Real",])
        my.df <- with(my.df, my.df[, !(colnames(my.df) == "type")])
        my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
        my.df <- add_label(my.df, "walk.type", my.name)
        my.res <- rbind(my.res, my.df)
    }
    return(my.res)
}

plot_capacity_dependence <- function(my.df, my.type)
{
    if (my.type == "buffered") {
        my.anno <- ddply(my.df, c("walk.type", "capacity"), summarise,
                         total=sum(backlog))
    }
    else if (my.type == "deletory") {
        my.anno <- ddply(my.df, c("walk.type", "capacity"), summarise,
                         total=sum(removed))
    }
    else {
        cat("unknown")
    }
    my.plot <- ggplot(my.anno, aes(x=capacity, y=total,
                                   colour=walk.type, group=walk.type))
    my.plot <- my.plot + geom_line() + geom_point()
    return(my.plot)
}

plot_capacity_exponent_dependence <- function(my.df)
{
    my.anno <- ddply(my.df, c("walk.type", "capacity"), fit_slope)
    my.plot <- ggplot(my.anno, aes(x=capacity, y=slope,
                                  ymin=slope - standard.error,
                                  ymax=slope + standard.error,
                                  colour=walk.type, group=walk.type))
    my.plot <- my.plot + geom_errorbar() + geom_point() + geom_line()
    return(my.plot)
}