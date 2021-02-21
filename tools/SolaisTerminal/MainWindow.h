#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QtWidgets/QLabel>
#include "AnnotatedMatViewer.h"
#include "ArmorDetector.h"
#include "ValueUIBindings.hpp"

namespace Ui {
class MainWindow;
}

namespace meta {

class MainWindow : public QMainWindow {
Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);

    ~MainWindow();

protected:

    bool eventFilter(QObject *obj, QEvent *event) override;

private:
    Ui::MainWindow *ui;

    ArmorDetector::ParameterSet params;
    ArmorDetector detector;

    static void showCVMatInLabel(const cv::Mat &mat, QImage::Format format, QLabel *label);

    void setUIFromResults() const;

    std::vector<ValueUIBinding *> bindings;

    std::vector<AnnotatedMatViewer *> viewers;

private slots:

    void runSingleDetection();

    void updateUIFromParams();

    void updateParamsFromUI();
};

}

#endif // MAINWINDOW_H
