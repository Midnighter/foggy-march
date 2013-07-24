library(ggplot2)


# Globals -----------------------------------------------------------------


my.brewer <- c("Real"="#E41A1C",
               "Internal"="#377EB8",
               "External"="#4DAF4A"
)
my.shapes <- c("Real"=16,
               "Internal"=4,
               "External"=3
)
my.lty <- c("Real"=1,
               "Internal"=2,
               "External"=3
)


# Layouts -----------------------------------------------------------------


layout_scaling <- function(my.plot,
                           my.xlab=paste("X label"),
                           my.ylab=paste("Y label"),
                           my.legend="Group",
                           my.colour=my.brewer,
                           my.form=my.shapes,
                           my.a=1,
                           my.p_sz=2)
{
    my.plot <- my.plot + scale_x_log10(name=as.expression(bquote(.(my.xlab))))
    my.plot <- my.plot + scale_y_log10(name=as.expression(bquote(.(my.ylab))))
    my.plot <- my.plot + geom_point(alpha=my.a, size=my.p_sz)
    my.plot <- my.plot + scale_shape_manual(name=my.legend, values=my.form)
    my.plot <- my.plot + scale_colour_manual(name=my.legend, values=my.colour)
    # prevent alpha values in the plot from reducing visibility of the legend
    my.plot <- my.plot + guides(colour=guide_legend(override.aes=list(alpha=1)))
    return(my.plot)
}


# Plots -------------------------------------------------------------------


plot_scaling <- function(my.df, my.legend, my.sep="type", my.col=my.brewer,
                         my.form=my.shapes, my.line=my.lty)
{
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
    my.dist <- tail(my.sep, 1)
    my.plot <- ggplot(my.df, aes_string(x="mean", y="signal",
                                        colour=my.dist,
                                        shape=my.dist))
    my.plot <- layout_scaling(my.plot,
                              expression(paste("Mean Activity <", italic(f[i]), ">")),
                              expression(paste("Standard Deviation ", italic(sigma[f[i]]))),
                              my.legend, my.col, my.form)
    # visual guides
    my.plot <- my.plot + geom_abline(slope=1, colour="grey", linetype=1)
    my.plot <- my.plot + geom_abline(slope=1/2, colour="grey", linetype=2)
    # compute the slopes and create annotation data frame
    my.anno <- ddply(my.df, my.sep, fit_slope)
    my.anno$text.x <- numeric(nrow(my.anno))
    my.anno$text.y <- numeric(nrow(my.anno))
    my.anno$text <- character(nrow(my.anno))
    my.x <- max(my.df$mean) ^ 0.99
    my.y <- max(my.df$signal)
    for (i in 1:nrow(my.anno)) {
        my.anno$text.x[i] <- my.x
        my.anno$text.y[i] <- my.y ^ (0.1 * i) 
        my.anno$text[i] <- sprintf("alpha == %.3G %s %.3G", my.anno$slope[i],
                                   "%+-%", my.anno$standard.error[i])
    }
    my.plot <- my.plot + geom_text(mapping=aes(label=text, x=text.x, y=text.y),
                                   data=my.anno, show_guide=FALSE, parse=TRUE,
                                   hjust=1, size=3)
    my.plot <- my.plot + geom_abline(mapping=aes_string(intercept="intercept",
                                                 slope="slope", colour=my.dist,
                                                 linetype=my.dist),
                                     data=my.anno, show_guide=FALSE)
    my.plot <- my.plot + scale_linetype_manual(values=my.line)
    return(my.plot)
}

plot_capacity_dependence <- function(my.df, scale.values="actual")
{
    my.anno <- ddply(my.df, c("walk.type", "capacity_total"), summarise,
                     total=sum(stopped))
    if (scale.values == "max") {
        my.anno <- ddply(my.anno, "walk.type", summarise, total=total/max(total),
                         capacity_total=capacity_total)
    }
    else if (scale.values == "bothmax") {
        my.anno <- ddply(my.anno, "walk.type", summarise,
                         total=total / max(total),
                         capacity_total=capacity_total / max(capacity_total))
    }
    my.plot <- ggplot(my.anno, aes(x=capacity_total, y=total,
                                   colour=walk.type, group=walk.type,
                                   shape=walk.type))
    my.plot <- my.plot + geom_line()
    my.plot <- my.plot + geom_point()
    my.plot <- my.plot + scale_x_log10(name="Total Capacity")
    my.plot <- my.plot + scale_y_log10(name="Total Stopped Walkers")
    return(my.plot)
}

plot_capacity_exponent_dependence <- function(my.df)
{
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
    my.anno <- ddply(my.df, c("walk.type", "capacity_total"), fit_slope)
    my.plot <- ggplot(my.anno, aes(x=capacity_total, y=slope,
                                   ymin=slope - standard.error,
                                   ymax=slope + standard.error,
                                   colour=walk.type, group=walk.type,
                                   shape=walk.type))
    my.plot <- my.plot + geom_errorbar()
    my.plot <- my.plot + geom_point(size=2.5)
    my.plot <- my.plot + geom_line()
    my.plot <- my.plot + scale_y_continuous(name="Exponent")
    my.plot <- my.plot + scale_x_log10(name="Total Capacity")
    return(my.plot)
}

plot_degree_vs_stopped <- function(my.df)
{
    tmp <- my.df[my.df$stopped > 0,]
    my.plot <- ggplot(tmp, aes(x=degree, y=stopped, colour=capacity_total))
    my.plot <- my.plot + geom_point(shape=4, size=1.5, alpha=1/3)
    my.plot <- my.plot + scale_x_log10(name=expression(paste("Degree ", italic(K)[i])))
    my.plot <- my.plot + scale_y_log10(name="Stopped Walkers at Node i")
    my.plot <- my.plot + facet_wrap(~ walk.type, ncol=2)
    my.plot <- my.plot + scale_colour_gradient(trans="log", low="blue", high="red")
    my.plot <- my.plot + theme(strip.text.x=element_text(size=8))
    return(my.plot)
}

plot_node_stopped <- function(my.df, node)
{
    tmp <- my.df[my.df$node == node,]
    tmp <- tmp[tmp$stopped > 0,]
    #     tmp$capacity_total <- factor(tmp$capacity_total)
    my.plot <- ggplot(tmp, aes(x=capacity, y=stopped))
    my.plot <- my.plot + geom_point()
    my.plot <- my.plot + scale_y_log10()
    my.plot <- my.plot + facet_wrap(~ walk.type, ncol=2)
    return(my.plot)
}


# Output ------------------------------------------------------------------


write_pdf <- function(my.plot, my.path, my.title="", tall=1)
{
    my.w <- 8
    my.h <- 6 * tall
    pdf(file=paste(my.path, ".pdf", sep=""), title=my.title,
        width=my.w, height=my.h)
    print(my.plot)
    dev.off()
    return()
}
