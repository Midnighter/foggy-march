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


plot_scaling <- function(my.df, my.legend)
{
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
    my.plot <- ggplot(my.df, aes(x=mean, y=signal, colour=type, shape=type))
    my.plot <- layout_scaling(my.plot,
                              expression(paste("Mean Activity <", italic(f[i]), ">")),
                              expression(paste("Standard Deviation ", italic(sigma[f[i]]))),
                              my.legend)
    # visual guides
    my.plot <- my.plot + geom_abline(slope=1, colour="grey", linetype=1)
    my.plot <- my.plot + geom_abline(slope=1/2, colour="grey", linetype=2)
    # compute the slopes and create annotation data frame
    my.anno <- ddply(my.df, "type", fit_slope)
    my.anno$text.x <- numeric(nrow(my.anno))
    my.anno$text.y <- numeric(nrow(my.anno))
    my.anno$text <- character(nrow(my.anno))
    my.x <- x_pos(my.df$mean)
    my.y <- y_pos(my.df$signal)
    for (i in 1:nrow(my.anno)) {
        my.anno$text.x[i] <- my.x
        my.anno$text.y[i] <- my.y * (0.5 ^ (i - 1)) 
        my.anno$text[i] <- sprintf("alpha == %.3G %s %.3G", my.anno$slope[i],
                                   "%+-%", my.anno$standard.error[i])
    }
    my.plot <- my.plot + geom_text(mapping=aes(label=text, x=text.x, y=text.y),
                                   data=my.anno, show_guide=FALSE, parse=TRUE,
                                   hjust=1)
    my.plot <- my.plot + geom_abline(mapping=aes(intercept=intercept,
                                                 slope=slope, linetype=type,
                                                 colour=type), data=my.anno,
                                     show_guide=FALSE)
    my.plot <- my.plot + scale_linetype_manual(values=my.lty)
    return(my.plot)
}

plot_capacity_dependence <- function(my.df)
{
    my.anno <- ddply(my.df, c("walk.type", "capacity_total"), summarise,
                     total=sum(stopped))
#     my.anno <- ddply(my.anno, "walk.type", summarise, total=total/max(total),
#                      capacity_total=capacity_total)
#     my.anno$total <- (my.anno$total - min(my.anno$total)) / (max(my.anno$total) - min(my.anno$total))
    my.plot <- ggplot(my.anno, aes(x=capacity_total, y=total,
                                   colour=walk.type, group=walk.type,
                                   shape=walk.type))
    my.plot <- my.plot + geom_line() + geom_point()
    return(my.plot)
}

plot_capacity_exponent_dependence <- function(my.df)
{
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(signal)),])
    my.anno <- ddply(my.df, c("walk.type", "capacity"), fit_slope)
    my.plot <- ggplot(my.anno, aes(x=capacity, y=slope,
                                   ymin=slope - standard.error,
                                   ymax=slope + standard.error,
                                   colour=walk.type, group=walk.type,
                                   shape=walk.type))
    my.plot <- my.plot + geom_errorbar() + geom_point() + geom_line()
    return(my.plot)
}


# Output ------------------------------------------------------------------


write_pdf <- function(my.plot, my.path, my.title="", tall=1)
{
    my.w <- 7
    my.h <- 7 * tall
    pdf(file=paste(my.path, ".pdf", sep=""), title=my.title,
        width=my.w, height=my.h)
    print(my.plot)
    dev.off()
    return()
}
