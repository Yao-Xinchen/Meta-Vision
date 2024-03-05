/*
 * Created by liuzikai on 4/16/20.
 * Reference: https://blog.csdn.net/Loser__Wang/article/details/51811347
 *
 * Usage:
 * Set camera parameters and calibration parameters below
 * Run the program and see the result
 * Parameters are saved as ../../../data/params/<width>x<height>.xml using cv::FileStorage
 * Press ESC to exit
 */

#include <iostream>
#include <opencv2/opencv.hpp>

using namespace cv;
using namespace std;

const int cameraIndex = 0;
const int cameraWidth = 1280;
const int cameraHeight = 1024;
const int cameraFPS = 211;

int main() {
    VideoCapture inputVideo(cameraIndex);

    if (!inputVideo.isOpened()) {
        cout << "Could not open the input video " << endl;
        return -1;
    }

    inputVideo.set(CAP_PROP_FRAME_WIDTH, cameraWidth);
    inputVideo.set(CAP_PROP_FRAME_HEIGHT, cameraHeight);
    inputVideo.set(CAP_PROP_FOURCC, VideoWriter::fourcc('M', 'J', 'P', 'G'));
    inputVideo.set(CAP_PROP_FPS, cameraFPS);

    cout << inputVideo.get(CAP_PROP_FRAME_WIDTH) << "x"
         << inputVideo.get(CAP_PROP_FRAME_HEIGHT) << "@"
         << inputVideo.get(CAP_PROP_FPS);

    Mat frame;
    Mat frameCalibration;

    inputVideo >> frame;

    /*
     >> cameraParams.IntrinsicMatrix

        ans =

          342.3936         0         0
           -0.0265  342.2803         0
          320.3885  174.8987    1.0000
     */
    /*Mat cameraMatrix = Mat::eye(3, 3, CV_64F);
    cameraMatrix.at<double>(0, 0) = 342.3936;
    cameraMatrix.at<double>(0, 1) = -0.0265;
    cameraMatrix.at<double>(0, 2) = 320.3885;
    cameraMatrix.at<double>(1, 1) = 342.2803;
    cameraMatrix.at<double>(1, 2) = 174.8987;*/


    Mat cameraMatrix = Mat::eye(3, 3, CV_64F);
    cameraMatrix.at<double>(0, 0) = 1.3844E3;
    cameraMatrix.at<double>(0, 1) = 0;
    cameraMatrix.at<double>(0, 2) = 0.6167E3;
    cameraMatrix.at<double>(1, 1) = 1.3799E3;
    cameraMatrix.at<double>(1, 2) = 0.4678E3;

    /*
     >> cameraParams.RadialDistortion

        ans =

            0.0396   -0.0614

        >> cameraParams.TangentialDistortion

        ans =

            0.0008   -0.0012
     */

    /*Mat distCoeffs = Mat::zeros(5, 1, CV_64F);
    distCoeffs.at<double>(0, 0) = 0.0396;
    distCoeffs.at<double>(1, 0) = -0.0614;
    distCoeffs.at<double>(2, 0) = 0.0008;
    distCoeffs.at<double>(3, 0) = -0.0012;
    distCoeffs.at<double>(4, 0) = 0;*/

    Mat distCoeffs = Mat::zeros(5, 1, CV_64F);
    distCoeffs.at<double>(0, 0) = -0.0697;
    distCoeffs.at<double>(1, 0) = 0.1052;
    distCoeffs.at<double>(2, 0) = 0;
    distCoeffs.at<double>(3, 0) = 0;
    distCoeffs.at<double>(4, 0) = 0;

    float zScale = 0.5;

    FileStorage fs("../../../data/params/" + std::to_string(cameraWidth) + "x" + std::to_string(cameraHeight) + ".xml", FileStorage::WRITE);
    fs << "cameraMatrix" << cameraMatrix;
    fs << "distCoeffs" << distCoeffs;
    fs << "zScale" << zScale;
    fs.release();

    Mat view, rview, map1, map2;
    Size imageSize;
    imageSize = frame.size();
    initUndistortRectifyMap(cameraMatrix, distCoeffs, Mat(),
                            getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, imageSize, 1, imageSize, 0),
                            imageSize, CV_16SC2, map1, map2);


    while (true) //Show the image captured in the window and repeat
    {
        inputVideo >> frame;              // read
        if (frame.empty()) break;         // check if at end
        remap(frame, frameCalibration, map1, map2, INTER_LINEAR);
        imshow("Original", frame);
        imshow("Calibration", frameCalibration);
        char key = waitKey(1);
        if (key == 27) break;
    }
    return 0;
}
