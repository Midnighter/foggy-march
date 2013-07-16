source("../analysis.R")
source("../plots.R")

my.path <- "Data"
my.out <- "Images"

pdf(file=paste(file.path(my.out, "all"), ".pdf", sep=""),
    title="", width=7, height=7 * 3 / 4)
for (my.name in list.files(my.path, "*.csv")) {
    my.df <- load_df(file.path(my.path, my.name))
    my.plot <- plot_scaling(my.df, "Signal")
    my.plot <- my.plot + ggtitle(sub(".csv", "", my.name))
    print(my.plot)
}
dev.off()

my.factors <- c(1, 2, 4, 8, 16)
my.res <- data.frame()
for (k in my.factors) {
#     my.name <- sprintf("buffered_uniform_random_walk_uniform_capacity_%d.csv", k)
#     my.name <- sprintf("buffered_uniform_random_walk_degree_capacity_%d.csv", k)
#     my.name <- sprintf("buffered_varied_uniform_random_walk_uniform_capacity_%d.csv", k)
#     my.name <- sprintf("buffered_varied_uniform_random_walk_degree_capacity_%d.csv", k)
#     my.name <- sprintf("deletory_uniform_random_walk_uniform_capacity_%d.csv", k)
#     my.name <- sprintf("deletory_uniform_random_walk_degree_capacity_%d.csv", k)
#     my.name <- sprintf("deletory_varied_uniform_random_walk_uniform_capacity_%d.csv", k)
    my.name <- sprintf("deletory_varied_uniform_random_walk_degree_capacity_%d.csv", k)
    my.df <- load_df(file.path(my.path, my.name))
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
    my.anno <- ddply(my.df, "type", fit_slope)
    my.anno$capacity <- rep(k, nrow(my.anno))
    my.res <- rbind(my.res, my.anno)
}

my.plot <- ggplot(my.res, aes(x=capacity, y=slope,
                              ymin=slope - standard.error,
                              ymax=slope + standard.error,
                              colour=type, group=type))
my.plot + geom_errorbar() + geom_point() + geom_line()