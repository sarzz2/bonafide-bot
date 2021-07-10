from matplotlib.ticker import FormatStrFormatter
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("TkAgg")


def plot(x, y):
    fig = plt.figure()
    fig.set_size_inches(15.5, 8.5)

    ax = fig.add_subplot(111)
    # set parameter color
    ax.tick_params(
        colors="white", which="both"
    )  # 'both' refers to minor and major axes

    # Format the datetime object
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))

    # display all the dates on x values
    plt.xticks(x)
    plt.margins(0)

    # rotate and align the tick labels so they look better
    fig.autofmt_xdate()
    ax.yaxis.grid()  # horizontal lines

    # plot the bar graph
    ax.bar(x, y, color="#71b3f5")

    ax.set_facecolor("#2e2e2e")
    fig.patch.set_facecolor("#2e2e2e")
    # Save the graph
    fig.savefig("foo.png", bbox_inches="tight")
