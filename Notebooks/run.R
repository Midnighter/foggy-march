source("../analysis.R")
source("../plots.R")

my.src <- "Tests"
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
my.buffered.levels <- c("buffered_uniform_random_walk_uniform_capacity"="buff. uni. cap.",
                       "buffered_uniform_random_walk_degree_capacity"="buff. d.-d. cap.",
                       "buffered_varied_uniform_random_walk_uniform_capacity"="buff. var., uni. cap.",
                       "buffered_varied_uniform_random_walk_degree_capacity"="buff. var., d.-d. cap.")

my.deletory.files <- c("deletory_uniform_random_walk_uniform_capacity",
                       "deletory_uniform_random_walk_degree_capacity",
                       "deletory_varied_uniform_random_walk_uniform_capacity",
                       "deletory_varied_uniform_random_walk_degree_capacity")
my.deletory.levels <- c("deletory_uniform_random_walk_uniform_capacity"="del. uni. cap.",
               "deletory_uniform_random_walk_degree_capacity"="del. d.-d. cap.",
               "deletory_varied_uniform_random_walk_uniform_capacity"="del. var., uni. cap.",
               "deletory_varied_uniform_random_walk_degree_capacity"="del. var., d.-d. cap.")

my.deleted <- load_capacity(my.src, my.deletory.files, my.deletory.levels)
my.buffered <- load_capacity(my.src, my.buffered.files, my.buffered.levels)
my.all <- rbind(my.deleted, my.buffered)

report <- function()
{
    my.plot <- plot_capacity_dependence(my.deleted)
    write_pdf(my.plot, file.path(my.out, "deletory_total_stopped"), tall=3/4)
    my.plot <- plot_capacity_dependence(my.buffered)
    write_pdf(my.plot, file.path(my.out, "buffered_total_stopped"), tall=3/4)
    
    my.plot <- plot_degree_vs_stopped(my.deleted)
    write_pdf(my.plot, file.path(my.out, "deletory_stopped_by_degree"), tall=3/4)
    my.plot <- plot_degree_vs_stopped(my.buffered)
    write_pdf(my.plot, file.path(my.out, "buffered_stopped_by_degree"), tall=3/4)
    
    my.plot <- plot_capacity_exponent_dependence(my.deleted)
    write_pdf(my.plot, file.path(my.out, "deletory_exponent_by_capacity"), tall=3/4)
    
    tmp <- transform_activity(my.deleted)
    tmp <- subset(tmp, type == "Real")
    
    my.plot <- plot_scaling(tmp, "Signal", c("walk.type", "capacity_total", "type"))
    my.plot <- my.plot + facet_grid("capacity_total ~ walk.type")
    my.plot <- my.plot + theme(strip.text.x=element_text(size=4),
                               strip.text.y=element_text(size=4),
                               axis.text.y=element_text(size=4),
                               axis.text.y=element_text(size=4))
    write_pdf(my.plot, file.path(my.out, "deletory_real_scaling"), tall=3/4)
    
    my.plot <- plot_capacity_exponent_dependence(my.buffered)
    write_pdf(my.plot, file.path(my.out, "buffered_exponent_by_capacity"), tall=3/4)
    
    tmp <- transform_activity(my.buffered)
    tmp <- subset(tmp, type == "Real")
    
    my.plot <- plot_scaling(tmp, "Signal", c("capacity_total", "walk.type", "type"))
    my.plot <- my.plot + facet_grid("capacity_total ~ walk.type")
    my.plot <- my.plot + theme(strip.text.x=element_text(size=4),
                               strip.text.y=element_text(size=4),
                               axis.text.y=element_text(size=4),
                               axis.text.y=element_text(size=4))
    write_pdf(my.plot, file.path(my.out, "buffered_real_scaling"), tall=3/4)
}
