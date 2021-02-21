#include "MainWindow.h"
#include "ui_MainWindow.h"

namespace meta {

MainWindow::MainWindow(QWidget *parent) :
        QMainWindow(parent),
        ui(new Ui::MainWindow) {
    ui->setupUi(this);

    bindings = {

            // ================================ Brightness Filter ================================

            new ValueCheckSpinBinding<double>(
                    nullptr, &params.brightnessThreshold,
                    nullptr, ui->brightnessSpin),

            // ================================ Color Filter ================================

            new EnumRadioBinding<ArmorDetector::ColorThresholdMode>(
                    &params.colorThresholdMode,
                    std::vector<std::pair<ArmorDetector::ColorThresholdMode, QRadioButton *>>{
                            {ArmorDetector::HSV,         ui->hsvRadio},
                            {ArmorDetector::RB_CHANNELS, ui->rbChannelRadio},
                    }),
            new RangeCheckSpinBinding<double>(
                    nullptr, &params.hsvRedHue,
                    nullptr, ui->hsvRedHueMinSpin, ui->hsvRedHueMaxSpin),
            new RangeCheckSpinBinding<double>(
                    nullptr, &params.hsvBlueHue,
                    nullptr, ui->hsvBlueHueMinSpin, ui->hsvBlueHueMaxSpin),
            new ValueCheckSpinBinding<double>(
                    nullptr, &params.rbChannelThreshold,
                    nullptr, ui->rbChannelThresholdSpin),
            new ValueCheckSpinBinding<int>(
                    &params.enableColorDilate, &params.colorDilate,
                    ui->colorDliateCheck, ui->colorDliateSpin),

            // ================================ Contour Filter ================================

            new EnumRadioBinding<ArmorDetector::ContourFitFunction>(
                    &params.contourFitFunction,
                    std::vector<std::pair<ArmorDetector::ContourFitFunction, QRadioButton *>>{
                            {ArmorDetector::MIN_AREA_RECT, ui->minAreaRectRadio},
                            {ArmorDetector::ELLIPSE,       ui->fitEllipseRadio},
                    }),
            new ValueCheckSpinBinding<double>(
                    &params.filterContourPixelCount, &params.contourPixelCount,
                    ui->contourPixelMinCountCheck, ui->contourPixelMinCountSpin),
            new ValueCheckSpinBinding<double>(
                    &params.filterContourMinArea, &params.contourMinArea,
                    ui->contourMinAreaCheck, ui->contourMinAreaSpin),
            new ValueCheckSpinBinding<int>(
                    &params.filterLongEdgeMinLength, &params.longEdgeMinLength,
                    ui->longEdgeMinLengthCheck, ui->longEdgeMinLengthSpin),
            new RangeCheckSpinBinding<double>(&params.filterLightAspectRatio, &params.lightAspectRatio,
                                              ui->aspectRatioFilterCheck, ui->aspectRatioMinSpin,
                                              ui->aspectRatioMaxSpin),

            // ================================ Armor Filter ================================

            new ValueCheckSpinBinding<double>(&params.filterLightLengthRatio, &params.lightLengthMaxRatio,
                                              ui->lightLengthRatioCheck, ui->lightLengthRatioMaxSpin),
            new RangeCheckSpinBinding<double>(&params.filterLightXDistance, &params.lightXDistOverL,
                                              ui->lightXDiffCheck, ui->lightXDiffMinSpin, ui->lightXDiffMaxSpin),

            new RangeCheckSpinBinding<double>(&params.filterLightYDistance, &params.lightYDistOverL,
                                              ui->lightYDiffCheck, ui->lightYDiffMinSpin, ui->lightYDiffMaxSpin),
            new ValueCheckSpinBinding<double>(&params.filterLightAngleDiff, &params.lightAngleMaxDiff,
                                              ui->lightAngleDiffCheck, ui->lightAngleDiffMaxSpin),
            new RangeCheckSpinBinding<double>(&params.filterArmorAspectRatio, &params.armorAspectRatio,
                                              ui->armorAspectRatioCheck, ui->armorAspectRatioMinSpin,
                                              ui->armorAspectRatioMaxSpin),
    };

    updateUIFromParams();

    connect(ui->runSingleButton, &QPushButton::clicked, this, &MainWindow::runSingleDetection);

    ui->contourImageWidget->installEventFilter(this);
}

MainWindow::~MainWindow() {
    for (auto &binding : bindings) delete binding;
    for (auto &viewer : viewers) delete viewer;
    delete ui;
}

void MainWindow::updateUIFromParams() {
    for (auto &binding : bindings) {
        binding->param2UI();
    }
}

void MainWindow::updateParamsFromUI() {
    for (auto &binding : bindings) {
        binding->ui2Params();
    }
}

void MainWindow::runSingleDetection() {
    updateParamsFromUI();
    detector.setParams(params);
    detector.detect(cv::imread("/Users/liuzikai/Files/VOCdevkit/VOC/JPEGImages/305.jpg"));
    setUIFromResults();
}

void MainWindow::setUIFromResults() const {
    showCVMatInLabel(detector.imgOriginal, QImage::Format_BGR888, ui->originalImage);
    showCVMatInLabel(detector.imgBrightnessThreshold, QImage::Format_Indexed8, ui->brightnessThresholdImage);
    showCVMatInLabel(detector.imgColorThreshold, QImage::Format_Indexed8, ui->colorThresholdImage);
    showCVMatInLabel(detector.noteContours.mat(), QImage::Format_BGR888, ui->contourImage);
    ui->contourCountLabel->setNum(detector.acceptedContourCount);
    showCVMatInLabel(detector.imgArmors, QImage::Format_BGR888, ui->armorImage);
}

void MainWindow::showCVMatInLabel(const cv::Mat &mat, QImage::Format format, QLabel *label) {
    auto img = QImage(mat.data, mat.cols, mat.rows, format);
    label->setPixmap(QPixmap::fromImage(img).scaledToHeight(label->height(), Qt::SmoothTransformation));
}

bool MainWindow::eventFilter(QObject *obj, QEvent *event) {
    if (obj == ui->contourImageWidget) {
        if (event->type() == QEvent::MouseButtonDblClick) {
            viewers.emplace_back(new AnnotatedMatViewer(detector.noteContours, QImage::Format_BGR888));
            viewers.back()->show();
        }
    }
    return QObject::eventFilter(obj, event);
}

}