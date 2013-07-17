library(reshape2)
library(plyr)


# Utility -----------------------------------------------------------------


add_label <- function(my.df, my.var, my.label)
{
    # add new label column to data frame
    if (is.numeric(my.label)) {
        my.df[[my.var]] <- rep(my.label, nrow(my.df))
    }
    else if (is.character(my.label)) {
        my.df[[my.var]] <- factor(rep(0, nrow(my.df)), labels=my.label)
    }
    my.df
}

transform_activity <- function(my.df)
{
    my.df <- melt(my.df, measure.vars=c("external", "internal", "std"),
                  variable.name="type", value.name="signal")
    my.df$type <- factor(my.df$type, levels=c("std", "internal", "external"),
                         labels=c("Real", "Internal", "External"))
    return(my.df)
}

load_capacity <- function(my.path, my.files)
{
    my.res <- data.frame()
    for (my.name in my.files) {
        my.file <- file.path(my.path, paste(my.name, ".csv", sep=""))
        if (!file.exists(my.file)) {
            next
        }
        my.df <- read.table(my.file, header=TRUE, sep=",")
#         my.df$capacity_total <- factor(my.df$capacity_total)
        my.df <- add_label(my.df, "walk.type", my.name)
        my.res <- rbind(my.res, my.df)
    }
    return(my.res)
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
