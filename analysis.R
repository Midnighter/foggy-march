library(reshape2)
library(plyr)


# Utility -----------------------------------------------------------------


load_df <- function(my.path)
{
    my.df <- read.table(my.path, header=TRUE, sep=",")
    my.df <- melt(my.df, measure.vars=c("external", "internal", "std"),
                  variable.name="type", value.name="signal")
    my.df$type <- factor(my.df$type, levels=c("std", "internal", "external"),
                         labels=c("Real", "Internal", "External"))
    return(my.df)
}

x_pos <- function(x)
{
    my.x <- log10(x)
    my.max <- max(my.x)
    my.pos <- my.max * 0.99
    return(10 ^ my.pos)
}

y_pos <- function(x)
{
    my.x <- log10(x)
    my.max <- max(my.x)
    my.pos <- my.max * 0.8
    return(10 ^ my.pos)
}

fit_slope <- function(my.df)
{
    my.fit <- summary(glm("signal ~ log(mean)", family=gaussian(link=log),
                          data=my.df))
    my.coef <- coefficients(my.fit)
    return(data.frame(slope=my.coef["log(mean)", "Estimate"],
                      standard.error=my.coef["log(mean)", "Std. Error"],
                      p.value=my.coef["log(mean)", "Pr(>|t|)"],
                      intercept=my.coef["(Intercept)", "Estimate"],
                      int.error=my.coef["(Intercept)", "Std. Error"]))
}
