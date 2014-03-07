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
my.comp.brewer <- c("companya"="#E41A1C",
                    "tdata"="#377EB8",
                    "lisega"="#4DAF4A",
                    "blg"="#984EA3",
                    "daimler"="#FF7F00",
                    "companyh"="#A65628"
                    )
my.comp.num <- c("companya"=1,
                 "tdata"=2,
                 "lisega"=3,
                 "blg"=4,
                 "daimler"=5,
                 "companyh"=6
                 )


# Layouts -----------------------------------------------------------------


layout_indi <- function(my.plot,
                        my.col,
                        my.shp,
                        my.xlab=expression(paste("Mean Activity <", italic(f[i]), ">")),
                        my.ylab=expression(paste("Standard Deviation ", italic(sigma[f[i]]))),
                        my.a=1,
                        my.p_sz=2)
{
    my.plot <- my.plot + scale_x_log10(name=as.expression(bquote(.(my.xlab))))
    my.plot <- my.plot + scale_y_log10(name=as.expression(bquote(.(my.ylab))))
    my.plot <- my.plot + geom_point(alpha=my.a, size=my.p_sz)
    my.plot <- my.plot + scale_shape_manual(values=my.shp)
    my.plot <- my.plot + scale_colour_manual(values=my.col)
    my.plot <- my.plot + theme(legend.position="none")
    return(my.plot)
}


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


plot_scaling <- function(my.df, my.legend, mean="mean", signal="signal",
                         my.sep="type", my.col=my.brewer,
                         my.form=my.shapes, my.line=my.lty,
                         my.fit="signal ~ log(mean)", my.fam=gaussian(link=log))
{
    my.df <- my.df[is.finite(log10(my.df[[mean]])) & is.finite(log10(my.df[[signal]])),]
    my.dist <- tail(my.sep, 1)
    my.plot <- ggplot(my.df, aes_string(x=mean, y=signal,
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
    my.anno <- ddply(my.df, my.sep, fit_slope, my.fit, my.fam)
    my.anno$text.x <- numeric(nrow(my.anno))
    my.anno$text.y <- numeric(nrow(my.anno))
    my.anno$text <- character(nrow(my.anno))
    my.x <- max(my.df[[mean]]) ^ 0.99
    my.y <- max(my.df[[signal]])
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
    my.df <- with(my.df, my.df[is.finite(log10(mean)) & is.finite(log10(std)),])
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

plot_total_activity <- function(my.df, my.act, my.legend, my.col, my.shp,
                                my.h=1, my.t=340)
{
    my.df <- ddply(my.df, c("time", "name"), function(df) {
        df$x <- 1:length(df[[my.act]])
        df[[my.act]] <- df[[my.act]]
        df$cutoff <- rep(my.t, nrow(df)) / as.numeric(as.character(unique(df$time)))
        return(df)
    })
    my.plot <- ggplot(my.df, aes_string(x="x", y=my.act, colour="name",
                           shape="name", group="name"))
    my.plot <- my.plot + geom_point()
    my.plot <- my.plot + scale_x_continuous(name=expression(paste("Bin ", t)))
    my.plot <- my.plot + scale_y_log10(name="System Activity")
    my.plot <- my.plot + geom_hline(yintercept=my.h)
    my.plot <- my.plot + geom_vline(aes(xintercept=cutoff))
    my.plot <- my.plot + facet_wrap(~ time, scales="free")
    my.plot <- my.plot + scale_shape_manual(name=my.legend, values=my.shp)
    my.plot <- my.plot + scale_colour_manual(name=my.legend, values=my.col)
    return(my.plot)
}

indi_slopes <- function(my.df, my.x, my.y, my.num, my.col)
{
    mask <- is.finite(log10(my.df[[my.x]])) & is.finite(log10(my.df[[my.y]]))
    my.df <- my.df[mask,]
    for (my.n in levels(my.df$name)) {
        tmp <- subset(my.df, name == my.n)
        if (nrow(tmp) == 0) {
            next
        }
        for (my.t in levels(my.df$time)) {
            my.sub <- subset(tmp, time == my.t)
            if (nrow(my.sub) == 0) {
                next
            }
            # slope fit methods
            # 1
            my.anno <- fit_slope(my.sub, sprintf("%s ~ log(%s)", my.y, my.x))
            my.anno$method <- "link=log"
            my.res <- my.sub
            my.res[[my.y]] <- (my.sub[[my.x]] ^ my.anno$slope)# * my.anno$intercept
            my.res$ucl <- my.sub[[my.x]] ^ (my.anno$slope + my.anno$standard.error)
            my.res$lcl <- my.sub[[my.x]] ^ (my.anno$slope - my.anno$standard.error)
            my.res$method <- rep(my.anno$method, nrow(my.res))
            # 2
            my.br <- 2 ^ seq(1, 10, length.out=30)
            my.tmp.x <- tapply(my.sub[[my.x]], findInterval(my.sub[[my.x]],
                                min(my.sub[[my.x]]) * my.br), mean)
            my.tmp.y <- tapply(my.sub[[my.y]], findInterval(my.sub[[my.y]],
                                min(my.sub[[my.y]]) * my.br), mean)
            my.bin <- data.frame(cbind(my.tmp.x, my.tmp.y))
            colnames(my.bin) <- c(my.x, my.y)
            my.anno2 <- fit_slope(my.bin, sprintf("%s ~ %s", my.y, my.x),
                                  my.fam=gaussian())
            my.anno2$method <- "log bin -> linear fit"
            my.anno <- rbind(my.anno, my.anno2)
            my.res2 <- my.sub
            my.res2[[my.y]] <- (my.sub[[my.x]] ^ my.anno2$slope)# * my.anno2$intercept
            my.res2$ucl <- my.sub[[my.x]] ^ (my.anno2$slope + my.anno2$standard.error)
            my.res2$lcl <- my.sub[[my.x]] ^ (my.anno2$slope - my.anno2$standard.error)
            my.res2$method <- rep(my.anno2$method, nrow(my.res2))
            my.res <- rbind(my.res, my.res2)
            # log of data
            my.sub2 <- my.sub
            my.sub2[[my.x]] <- log10(my.sub[[my.x]])
            my.sub2[[my.y]] <- log10(my.sub[[my.y]])
            # 1
            my.anno2 <- fit_slope(my.sub2, sprintf("%s ~ %s", my.y, my.x),
                                 my.fam=gaussian())
            my.anno2$method <- "log -> linear fit"
            my.anno <- rbind(my.anno, my.anno2)
            my.res2 <- my.sub
            my.res2[[my.y]] <- (my.sub[[my.x]] ^ my.anno2$slope)# * my.anno2$intercept
            my.res2$ucl <- my.sub[[my.x]] ^ (my.anno2$slope + my.anno2$standard.error)
            my.res2$lcl <- my.sub[[my.x]] ^ (my.anno2$slope - my.anno2$standard.error)
            my.res2$method <- rep(my.anno2$method, nrow(my.res2))
            my.res <- rbind(my.res, my.res2)
            # 2
#             my.tmp.x <- tapply(my.sub2[[my.x]],
#                     findInterval(my.sub2[[my.x]],
#                     seq(min(my.sub2[[my.x]]), max(my.sub2[[my.x]]), length.out=100)), mean)
#             my.tmp.x <- my.tmp.x[my.tmp.x > 0]
#             my.tmp.y <- tapply(my.sub2[[my.y]],
#                     findInterval(my.sub2[[my.y]],
#                     seq(min(my.sub2[[my.y]]), max(my.sub2[[my.y]]), length.out=100)), mean)
#             my.tmp.y <- my.tmp.y[my.tmp.y > 0]
#             print(cbind(my.tmp.x, my.tmp.y))
#             my.bin <- data.frame(my.tmp.x, my.tmp.y)
#             colnames(my.bin) <- c(my.x, my.y)
#             my.anno2 <- fit_slope(my.bin, sprintf("%s ~ %s", my.y, my.x),
#                                   my.fam=gaussian())
#             my.anno2$method <- "log -> linear bin -> linear fit"
#             my.anno <- rbind(my.anno, my.anno2)
#             my.res2 <- my.sub
#             my.res2[[my.y]] <- (my.sub[[my.x]] ^ my.anno2$slope)# * my.anno2$intercept
#             my.res2$ucl <- my.sub[[my.x]] ^ (my.anno2$slope + my.anno2$standard.error)
#             my.res2$lcl <- my.sub[[my.x]] ^ (my.anno2$slope - my.anno2$standard.error)
#             my.res2$method <- rep(my.anno2$method, nrow(my.res))
#             my.res <- rbind(my.res, my.res2)
            # factorise
            my.anno$method <- factor(my.anno$method)
            my.res$method <- factor(my.res$method)
            # plot fits
            my.plot <- ggplot(my.res, aes_string(x=my.x, y=my.y,
                                           linetype="method",
                                           colour="method",
                                           group="method"))
            my.plot <- my.plot + geom_line()
            my.plot <- my.plot + geom_smooth(aes(ymin=lcl, ymax=ucl), stat="identity")
            my.plot <- my.plot + scale_x_log10(name=expression(paste("Mean Activity <", italic(f[i]), ">")))
            my.plot <- my.plot + scale_y_log10(name=expression(paste("Standard Deviation ", italic(sigma[f[i]]))))
            my.plot <- my.plot + scale_colour_brewer(name="Method", palette="Set1")
            my.plot <- my.plot + scale_linetype_discrete(name="Method")
            # data points
            my.plot <- my.plot + geom_point(data=my.sub,
                                            mapping=aes_string(x=my.x, y=my.y,
                                                               slope=NULL,
                                                               intercept=NULL,
                                                               linetype=NULL,
                                                               colour=NULL,
                                                               group=NULL),
                                            shape=4, alpha=1, size=2)
#             my.plot <- my.plot + geom_point(data=my.bin,
#                                             mapping=aes_string(x=10 ^ my.x,
#                                                                y=10 ^ my.y,
#                                                                slope=NULL,
#                                                                intercept=NULL,
#                                                                linetype=NULL,
#                                                                colour=NULL,
#                                                                group=NULL),
#                                             shape=3, alpha=1, size=2, colour="red")
            print(my.plot)
        }
    }
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
