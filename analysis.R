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

load_capacity <- function(my.path, my.files, my.levels)
{
    my.res <- data.frame()
    for (my.name in my.files) {
        my.file <- file.path(my.path, paste(my.name, ".csv", sep=""))
        if (!file.exists(my.file)) {
            next
        }
        my.df <- read.table(my.file, header=TRUE, sep=",")
        my.df <- add_label(my.df, "walk.type", my.levels[my.name])
        my.res <- rbind(my.res, my.df)
    }
    return(my.res)
}

fit_slope <- function(my.df, my.formula="std ~ log(mean)", my.fam=gaussian(link=log))
{
    my.fit <- summary(glm(my.formula, family=my.fam, data=my.df, start=c(1, 1)))
    my.coef <- coefficients(my.fit)
    if (dim(my.coef)[1] < 2) {
        return(data.frame())
    }
    my.lbl <- attr(terms(as.formula(my.formula)), "term.labels")
    return(data.frame(slope=my.coef[my.lbl, "Estimate"],
                      standard.error=my.coef[my.lbl, "Std. Error"],
                      p.value=my.coef[my.lbl, "Pr(>|t|)"],
                      intercept=my.coef["(Intercept)", "Estimate"],
                      int.error=my.coef["(Intercept)", "Std. Error"]))
}

all_slopes <- function(my.df, mean, signal, my.sep=c("time", "name"),
                       my.formula="std_activity ~ log(mean_activity)",
                       my.fam=gaussian(link=log))
{
    my.df <- my.df[is.finite(log10(my.df[[mean]])) & is.finite(log10(my.df[[signal]])),]
    my.anno <- ddply(my.df, my.sep, fit_slope, my.formula, my.fam)
    return(my.anno)
}
