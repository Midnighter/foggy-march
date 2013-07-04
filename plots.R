library(ggplot2)


# Utility -----------------------------------------------------------------


my.brewer <- c("Real"="#E41A1C",
                      "Internal"="#377EB8",
                      "External"="#4DAF4A"
                      )
my.shapes <- c("Real"=16,
                      "Internal"=4,
                      "External"=3
                     )



# Plots -------------------------------------------------------------------


plot_relation <- function(my.df)
{
    my.plot <- ggplot(my.df) + scale_x_log10() + scale_y_log10()
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=std,
                                                colour="Real", shape="Real"),
                                    size=3, alpha=0.5)
    my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=std, colour="Real"),
                                     formula="y ~ log(x)", method="glm",
                                     family=gaussian(link=log))
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=internal,
                                                colour="Internal", shape="Internal"),
                                    size=3, alpha=0.5)
    my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=internal,
                                                 colour="Internal"),
                                     formula="y ~ log(x)", method="glm",
                                     family=gaussian(link=log))
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=external,
                                                colour="External", shape="External"),
                                    size=3, alpha=0.5)
    my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=external,
                                                 colour="External"),
                                     formula="y ~ log(x)", method="glm",
                                     family=gaussian(link=log))
    my.plot <- my.plot + guides(colour=guide_legend(override.aes=list(alpha=1)))
    my.plot <- my.plot + scale_shape_manual(values=my.shapes)
    my.plot <- my.plot + scale_colour_manual(values=my.brewer)
    my.plot <- my.plot + geom_abline(slope=1, colour="grey")
    my.plot <- my.plot + geom_abline(slope=1/2, colour="grey", linetype=2)
    return(my.plot)
}

plot_relation2 <- function(my.df)
{
    alpha <- numeric(3)
    se <- numeric(3)
    type <- character(3)
    fit.real <- summary(glm(std ~ log(mean), family=gaussian(link=log), data=my.df))
    se[1] <- coefficients(fit.real)["log(mean)", "Std. Error"]
    alpha[1] <- coefficients(fit.real)["log(mean)", "Estimate"]
    type[1] <- "Real"
    fit.int <- summary(glm(std ~ log(internal), family=gaussian(link=log), data=my.df))
    se[2] <- coefficients(fit.int)["log(internal)", "Std. Error"]
    alpha[2] <- coefficients(fit.int)["log(internal)", "Estimate"]
    type[2] <- "Internal"
    fit.ext <- summary(glm(std ~ log(external), family=gaussian(link=log), data=my.df))
    se[3] <- coefficients(fit.ext)["log(external)", "Std. Error"]
    alpha[3] <- coefficients(fit.ext)["log(external)", "Estimate"]
    type[3] <- "External"
    my.stat <- data.frame(alpha=alpha, se=se, type=type)
    print(my.stat)
    my.plot <- ggplot(my.df) + scale_x_log10() + scale_y_log10()
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=std,
                                                colour="Real", shape="Real"),
                                    size=3, alpha=0.5)
    
    my.plot <- my.plot + geom_ribbon(mapping=aes(x=mean, ymin=std - eval(my.stat$se[1], envir=environment()),
                                                 ymax=std + eval(my.stat$se[1], envir=environment())))
#     my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=std, colour="Real"),
#                                      formula="y ~ log(x)", method="glm",
#                                      family=gaussian(link=log))
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=internal,
                                                colour="Internal", shape="Internal"),
                                    size=3, alpha=0.5)
    
#     my.plot <- my.plot + geom_ribbon(mapping=aes(x=mean, ymin=std - my.stat$se[2],
#                                                  ymax=std + my.stat$se[2]))
#     my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=internal,
#                                                  colour="Internal"),
#                                      formula="y ~ log(x)", method="glm",
#                                      family=gaussian(link=log))
    my.plot <- my.plot + geom_point(mapping=aes(x=mean, y=external,
                                                colour="External", shape="External"),
                                    size=3, alpha=0.5)
#     my.plot <- my.plot + geom_smooth(mapping=aes(x=mean, y=external,
#                                                  colour="External"),
#                                      formula="y ~ log(x)", method="glm",
#                                      family=gaussian(link=log))
    my.plot <- my.plot + guides(colour=guide_legend(override.aes=list(alpha=1)))
    my.plot <- my.plot + scale_shape_manual(values=my.shapes)
    my.plot <- my.plot + scale_colour_manual(values=my.brewer)
    my.plot <- my.plot + geom_abline(slope=1, colour="grey")
    my.plot <- my.plot + geom_abline(slope=1/2, colour="grey", linetype=2)
    return(my.plot)
}
