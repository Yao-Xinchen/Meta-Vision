//
// Created by liuzikai on 3/28/21.
//

#ifndef META_VISION_SOLAIS_SERIAL_H
#define META_VISION_SOLAIS_SERIAL_H

#include <string>
#include <cstdint>
#include <boost/asio.hpp>
#include <utility>
#include "FrameCounterBase.h"
#include "Utilities.h"

namespace meta {

class Serial : public FrameCounterBase {
public:

    explicit Serial(boost::asio::io_context &ioContext);

    bool sendControlCommand(bool detected, bool topKillerTriggered, TimePoint time, float yawDelta, float pitchDelta, float distance,
                            float avgLightAngle, float imageX, float imageY, int remainingTimeToTarget, int period);

private:

    static constexpr uint8_t SOF = 0xA5;

    struct __attribute__((packed, aligned(1))) VisionCommand {

        enum VisionFlag : uint8_t {
            NONE = 0,
            DETECTED = 1,
            TOP_KILLER_TRIGGERED = 2,
        };

        uint8_t flag;
        uint16_t frameTime;             // [0.1ms]
        int16_t yawDelta;               // yaw relative angle [deg] * 100
        int16_t pitchDelta;             // pitch relative angle [deg] * 100
        int16_t distance;               // [mm]
        int16_t avgLightAngle;          // [deg] * 100
        int16_t imageX;                 // pixel
        int16_t imageY;                 // pixel
        int16_t remainingTimeToTarget;  // [ms]
        int16_t period;                 // [ms]
    };

    struct __attribute__((packed, aligned(1))) Package {
        uint8_t sof;  // start of frame, 0xA5
        uint8_t cmdID;
        union {  // union takes the maximal size of its elements
            VisionCommand command;
        };
        uint8_t crc8;  // just for reference but not use (the offset of this is not correct)
    };

    enum CommandID : uint8_t {
        VISION_CONTROL_CMD_ID = 0,
        CMD_ID_COUNT
    };

    static constexpr size_t DATA_SIZE[CMD_ID_COUNT] = {
            sizeof(VisionCommand)
    };

private:

    boost::asio::io_context &ioContext;
    boost::asio::serial_port serial;

    static constexpr int SERIAL_BAUD_RATE = 115200;

    enum ReceiverState {
        RECV_PREAMBLE,          // 0xA5
        RECV_CMD_ID,            // cmdID
        RECV_DATA_TAIL,         // data section and 1-byte CRC8
    };

    static constexpr size_t RECV_BUFFER_SIZE = 0x1000;
    ReceiverState recvState = RECV_PREAMBLE;

    uint8_t sendSeq = 0;

    Package recvPackage;

    void handleSend(std::shared_ptr<Package> buf, const boost::system::error_code &error, size_t numBytes);

    void handleRecv(const boost::system::error_code &error, size_t numBytes);

};
}

#endif //META_VISION_SOLAIS_SERIAL_H
