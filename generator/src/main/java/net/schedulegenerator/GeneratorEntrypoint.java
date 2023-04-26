package net.schedulegenerator;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.LambdaLogger;

import java.util.Map;


public class GeneratorEntrypoint implements RequestHandler<Map<String,String>, Void> {

    public GeneratorEntrypoint() {

    }

    @Override
    public Void handleRequest(Map<String, String> event, Context context) {
        LambdaLogger logger = context.getLogger();
        logger.log("EVENT TYPE: " + event.getClass());
        return null;
    }
}
